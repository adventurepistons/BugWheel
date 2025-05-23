const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const helmet = require('helmet');
const { extractLocators } = require('./locatorEngine');
const { exportResults } = require('./exportEngine');
const swaggerUi = require('swagger-ui-express');
const YAML = require('yamljs');
const morgan = require('morgan');
const admin = require('firebase-admin');
const serviceAccount = require('./firebase-service-account.json');
const rateLimit = require('express-rate-limit');
const { v4: uuidv4 } = require('uuid');
const Joi = require('joi');
const sanitizeHtml = require('sanitize-html');
const multer = require('multer');
require('dotenv').config();

const app = express();

app.use(helmet());
app.use(cors({
  origin: function (origin, callback) {
    // Allow requests with no origin (like mobile apps, curl, Postman)
    if (!origin) return callback(null, true);
    // Only allow production and staging domains (set in ALLOWED_ORIGINS)
    const allowedOrigins = (process.env.ALLOWED_ORIGINS || '').split(',').map(o => o.trim()).filter(Boolean);
    // Example: process.env.ALLOWED_ORIGINS = 'https://yourapp.com,https://staging.yourapp.com'
    if (allowedOrigins.length === 0 || allowedOrigins.includes(origin)) {
      return callback(null, true);
    }
    return callback(new Error('Not allowed by CORS'));
  },
  credentials: true,
}));
app.use(bodyParser.json({ limit: '10mb' }));

// --- Rate Limiting ---
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 50, // limit each IP to 50 requests per windowMs
  standardHeaders: true,
  legacyHeaders: false,
});
app.use(limiter); // Note: Rate limiting is per IP. For production, consider per-user rate limiting.

app.use(morgan('combined'));

// --- Firebase Auth Middleware ---
async function firebaseAuth(req, res, next) {
  // Allow unauthenticated access to /api/status and /api/v1/allowed-tags only
  if (req.path === '/api/status' || req.path === '/api/v1/allowed-tags') return next();
  const authHeader = req.headers['authorization'];
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return errorResponse(res, 'Unauthorized: Missing or invalid Authorization header.', 401);
  }
  const idToken = authHeader.split(' ')[1];
  try {
    const decodedToken = await admin.auth().verifyIdToken(idToken);
    // --- Enforce 1-hour session expiration ---
    const now = Math.floor(Date.now() / 1000); // seconds
    const maxAge = 60 * 60; // 1 hour in seconds
    if (decodedToken.iat && now - decodedToken.iat > maxAge) {
      return errorResponse(res, 'Session expired. Please sign in again.', 401);
    }
    req.user = decodedToken; // You can access user info in your handlers
    next();
  } catch (err) {
    return errorResponse(res, 'Unauthorized: Invalid Firebase ID token.', 401);
  }
}

app.use(firebaseAuth);

// Swagger UI setup (now protected)
const swaggerDocument = YAML.load('./swagger.yaml');
app.use('/docs', swaggerUi.serve, swaggerUi.setup(swaggerDocument));

// Health check
app.get('/api/status', (req, res) => {
  res.json({
    status: 'ok',
    version: '1.0.0',
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    timestamp: new Date().toISOString(),
  });
});

// In-memory scan history: { userId: [{ id, url, timestamp }] }
const scanHistory = {};
// In-memory scan results: { userId: { scanId: { elements, dom, url, timestamp } } }
const scanResults = {};

// --- Per-user rate limiting (50 scans per user per day) ---
const userScanCounts = {}; // { userId: { date: 'YYYY-MM-DD', count: number } }
const MAX_SCANS_PER_DAY = 50;

const elementSchema = Joi.object({
  tag: Joi.string().required(),
  id: Joi.string().allow(''),
  name: Joi.string().allow(''),
  type: Joi.string().allow(''),
  class: Joi.string().allow(''),
  text: Joi.string().allow(''),
  value: Joi.string().allow(''),
  aria_label: Joi.string().allow(''),
  role: Joi.string().allow(''),
  attributes: Joi.object().pattern(Joi.string(), Joi.string()),
});

// Allow all tags except risky ones, allow all attributes
const customSanitizeOptions = {
  allowedTags: false, // allow all tags except those in disallowedTags
  disallowedTagsMode: 'discard',
  disallowedTags: ['script', 'object', 'embed', 'style', 'link', 'base'], // iframe is allowed
  allowedAttributes: false, // allow all attributes
  allowedSchemes: ['http', 'https', 'mailto'],
  allowProtocolRelative: true
};

// Main endpoint for DOM processing
app.post('/api/v1/process-dom', async (req, res) => {
  // Per-user rate limiting
  const userId = req.user && req.user.uid ? req.user.uid : null;
  if (userId) {
    const today = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
    if (!userScanCounts[userId] || userScanCounts[userId].date !== today) {
      userScanCounts[userId] = { date: today, count: 0 };
    }
    if (userScanCounts[userId].count >= MAX_SCANS_PER_DAY) {
      return errorResponse(res, `Rate limit exceeded: Max ${MAX_SCANS_PER_DAY} scans per day.`, 429);
    }
    userScanCounts[userId].count++;
  }
  // Joi schema: either dom (string, min 1, max 500000) or elements (array, min 1, max 5000), at least one required
  const schema = Joi.object({
    dom: Joi.string().min(1).max(500000),
    elements: Joi.array().items(elementSchema).min(1).max(5000),
    url: Joi.string().uri().optional(),
    tags: Joi.array().items(Joi.string()).optional(),
  }).or('dom', 'elements');

  const { error } = schema.validate(req.body);
  if (error) {
    // Log validation error with user ID if available
    const userId = req.user && req.user.uid ? req.user.uid : 'anonymous';
    console.warn(`[WARN] Validation error for /api/process-dom by user ${userId}: ${error.details[0].message}`);
    return errorResponse(res, 'Invalid input: ' + error.details[0].message, 400);
  }
  try {
    let { dom, elements, url, tags } = req.body;
    // Sanitize DOM string if present
    if (dom) {
      dom = sanitizeHtml(dom, customSanitizeOptions);
    }
    // Timeout: 30 seconds max for processing
    const timeoutPromise = new Promise((_, reject) => setTimeout(() => reject(new Error('Processing timeout')), 30000));
    const results = await Promise.race([
      Promise.resolve(extractLocators({ dom, elements, tags })),
      timeoutPromise
    ]);
    // Remove circular references (parent, children) from each element
    const sanitized = results.map(({ parent, children, ...rest }) => rest);
    // --- Record scan in history and generate scanId ---
    let scanId = uuidv4();
    if (url && req.user && req.user.uid) {
      const userId = req.user.uid;
      if (!scanHistory[userId]) scanHistory[userId] = [];
      scanHistory[userId].push({
        id: scanId,
        url,
        timestamp: new Date().toISOString(),
      });
      // Store the full scan result
      if (!scanResults[userId]) scanResults[userId] = {};
      scanResults[userId][scanId] = {
        elements: sanitized,
        dom,
        url,
        timestamp: new Date().toISOString(),
      };
    }
    res.json({ elements: sanitized, scanId });
  } catch (err) {
    if (err.message === 'Processing timeout') {
      return errorResponse(res, 'Processing took too long. Please try with a smaller DOM.', 503);
    }
    res.status(500).json({ error: err.message });
  }
});

// Export endpoint
app.post('/api/v1/export', (req, res) => {
  // Joi validation for export
  const exportSchema = Joi.object({
    scanId: Joi.string().min(10).required(),
    format: Joi.string().valid('json', 'csv', 'xml', 'selenium', 'playwright').required(),
    tags: Joi.array().items(Joi.string()).optional(),
    elementIds: Joi.array().items(Joi.string()).optional(),
  });
  const { error } = exportSchema.validate(req.body);
  if (error) {
    return errorResponse(res, 'Invalid input: ' + error.details[0].message, 400);
  }
  try {
    if (!req.user || !req.user.uid) {
      return errorResponse(res, 'Unauthorized', 401);
    }
    const userId = req.user.uid;
    const { scanId, format, tags, elementIds } = req.body;
    const userResults = scanResults[userId] || {};
    const scan = userResults[scanId];
    if (!scan) {
      return errorResponse(res, 'Scan not found', 404);
    }
    let elements = scan.elements || [];
    // Filter by tags if provided
    if (tags && tags.length > 0) {
      elements = elements.filter(el => tags.includes(el.tag));
    }
    // Filter by elementIds if provided (match by id field)
    if (elementIds && elementIds.length > 0) {
      elements = elements.filter(el => elementIds.includes(el.id));
    }
    const exported = exportResults({ elements, format });
    res.json({ data: exported });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Accessibility endpoint
app.post('/api/v1/accessibility', async (req, res) => {
  try {
    // Accept either dom (string) or elements (array)
    const schema = Joi.object({
      dom: Joi.string().min(1),
      elements: Joi.array().items(elementSchema).min(1),
    }).or('dom', 'elements');
    const { error } = schema.validate(req.body);
    if (error) {
      return errorResponse(res, 'Invalid input: ' + error.details[0].message, 400);
    }
    let dom = req.body.dom;
    if (!dom && req.body.elements) {
      // Reconstruct DOM string from elements array
      dom = req.body.elements.map(el => {
        let attrs = '';
        if (el.attributes) {
          attrs = Object.entries(el.attributes).map(([k, v]) => ` ${k}="${v}"`).join('');
        }
        return `<${el.tag}${attrs}>${el.text || ''}</${el.tag}>`;
      }).join('');
    }
    if (!dom) return errorResponse(res, 'DOM string could not be constructed.', 400);
    const { JSDOM } = require('jsdom');
    const axe = require('axe-core');
    const jsdom = new JSDOM(dom, { runScripts: 'outside-only', resources: 'usable' });
    const { window } = jsdom;
    window.eval(axe.source);
    await new Promise(r => setTimeout(r, 100));
    const results = await window.axe.run(window.document);
    res.json({ audit: results });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// --- Scan History Endpoint ---
app.get('/api/v1/scan/history', (req, res) => {
  try {
    if (!req.user || !req.user.uid) {
      return errorResponse(res, 'Unauthorized', 401);
    }
    const userId = req.user.uid;
    const history = scanHistory[userId] || [];
    // Pagination
    const page = parseInt(req.query.page, 10) || 1;
    const pageSize = parseInt(req.query.pageSize, 10) || 20;
    const total = history.length;
    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    const paginated = history.slice(start, end).map(scan => ({
      id: scan.id,
      url: scan.url,
      timestamp: scan.timestamp,
    }));
    res.json({
      scans: paginated,
      total,
      page,
      pageSize,
      totalPages: Math.ceil(total / pageSize),
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// --- Delete Scan History Endpoint ---
app.delete('/api/v1/scan/history', (req, res) => {
  try {
    if (!req.user || !req.user.uid) {
      return errorResponse(res, 'Unauthorized', 401);
    }
    const userId = req.user.uid;
    scanHistory[userId] = [];
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// --- Scan Result by ID Endpoint ---
app.get('/api/v1/scan/result/:scanId', (req, res) => {
  try {
    if (!req.user || !req.user.uid) {
      return errorResponse(res, 'Unauthorized', 401);
    }
    const userId = req.user.uid;
    const { scanId } = req.params;
    if (!scanId || typeof scanId !== 'string' || scanId.length < 10) {
      return errorResponse(res, 'Invalid scanId', 400);
    }
    const userResults = scanResults[userId] || {};
    const result = userResults[scanId];
    if (!result) {
      return errorResponse(res, 'Scan result not found', 404);
    }
    // Return only necessary fields
    res.json({
      scanId,
      url: result.url,
      timestamp: result.timestamp,
      elements: result.elements,
      dom: result.dom,
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Helper: create a unique key for an element based on tag + sorted attributes
function elementKey(el) {
  if (!el || !el.tag || !el.attributes) return '';
  const attrs = Object.entries(el.attributes)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([k, v]) => `${k}=${v}`)
    .join('|');
  return `${el.tag}|${attrs}`;
}

// Helper: deep diff of two elements (returns changed properties)
function diffElements(a, b) {
  const diff = {};
  for (const key of Object.keys(a)) {
    if (key === 'attributes') {
      const aAttrs = a.attributes || {};
      const bAttrs = b.attributes || {};
      const attrDiff = {};
      const allAttrKeys = new Set([...Object.keys(aAttrs), ...Object.keys(bAttrs)]);
      for (const attr of allAttrKeys) {
        if (aAttrs[attr] !== bAttrs[attr]) {
          attrDiff[attr] = { from: aAttrs[attr], to: bAttrs[attr] };
        }
      }
      if (Object.keys(attrDiff).length > 0) diff.attributes = attrDiff;
    } else if (a[key] !== b[key]) {
      diff[key] = { from: a[key], to: b[key] };
    }
  }
  return diff;
}

// POST /api/v1/compare-scans
app.post('/api/v1/compare-scans', multer({
  limits: { fileSize: 2 * 1024 * 1024 }, // 2MB per file
  fileFilter: (req, file, cb) => {
    if (file.mimetype !== 'application/json') {
      return cb(new Error('Only JSON files are allowed'));
    }
    cb(null, true);
  },
}).fields([{ name: 'scanA', maxCount: 1 }, { name: 'scanB', maxCount: 1 }]), async (req, res) => {
  try {
    if (!req.files || !req.files.scanA || !req.files.scanB) {
      return errorResponse(res, 'Both scanA and scanB files are required.', 400);
    }
    const scanA = JSON.parse(req.files.scanA[0].buffer.toString('utf-8'));
    const scanB = JSON.parse(req.files.scanB[0].buffer.toString('utf-8'));
    if (!Array.isArray(scanA.elements) || !Array.isArray(scanB.elements)) {
      return errorResponse(res, 'Both files must contain an elements array.', 400);
    }
    // Build maps by element key
    const mapA = new Map(scanA.elements.map(el => [elementKey(el), el]));
    const mapB = new Map(scanB.elements.map(el => [elementKey(el), el]));
    // Find added, removed, changed
    const added = [];
    const removed = [];
    const changed = [];
    for (const [key, elB] of mapB.entries()) {
      if (!mapA.has(key)) {
        added.push({ key, element: elB });
      } else {
        const elA = mapA.get(key);
        const diff = diffElements(elA, elB);
        if (Object.keys(diff).length > 0) {
          changed.push({ key, before: elA, after: elB, diff });
        }
      }
    }
    for (const [key, elA] of mapA.entries()) {
      if (!mapB.has(key)) {
        removed.push({ key, element: elA });
      }
    }
    res.json({ added, removed, changed });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Feedback types for dropdown
const FEEDBACK_TYPES = ['bug', 'improvement', 'feature request', 'experience'];

const feedbackLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 10, // limit each IP to 10 requests per hour
  standardHeaders: true,
  legacyHeaders: false,
});

// POST /api/v1/feedback
app.post('/api/v1/feedback', feedbackLimiter, (req, res) => {
  const schema = Joi.object({
    type: Joi.string().valid(...FEEDBACK_TYPES).required(),
    description: Joi.string().min(5).required(),
    email: Joi.string().email().optional(),
    screenshot: Joi.string().base64().optional(),
    url: Joi.string().uri().optional(),
  });
  const { error } = schema.validate(req.body);
  if (error) {
    return errorResponse(res, 'Invalid input: ' + error.details[0].message, 400);
  }
  // For MVP: log feedback (replace with DB/email in production)
  console.log('User feedback:', {
    user: req.user && req.user.uid,
    ...req.body,
    time: new Date().toISOString(),
  });
  res.json({ success: true });
});

// POST /api/v1/error-report
app.post('/api/v1/error-report', feedbackLimiter, (req, res) => {
  const schema = Joi.object({
    error: Joi.string().required(),
    stack: Joi.string().optional(),
    url: Joi.string().uri().optional(),
    user: Joi.string().optional(),
    extra: Joi.object().optional(),
  });
  const { error } = schema.validate(req.body);
  if (error) {
    return errorResponse(res, 'Invalid input: ' + error.details[0].message, 400);
  }
  // For MVP: log error report (replace with DB/email in production)
  console.error('Error report:', {
    ...req.body,
    time: new Date().toISOString(),
  });
  res.json({ success: true });
});

// API usage logging middleware
app.use((req, res, next) => {
  if (!req.path.startsWith('/api/status') && !req.path.startsWith('/docs')) {
    const userId = req.user && req.user.uid ? req.user.uid : 'anonymous';
    console.log(`[API] ${req.method} ${req.path} by ${userId} at ${new Date().toISOString()}`);
  }
  next();
});

// Error logging middleware (should be after all routes)
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({ error: 'Internal server error.' });
});

// --- Allowed Tags Endpoint ---
app.get('/api/v1/allowed-tags', (req, res) => {
  // All HTML tags except those in disallowedTags
  const allHtmlTags = [
    'a','abbr','address','area','article','aside','audio','b','base','bdi','bdo','blockquote','body','br','button','canvas','caption','cite','code','col','colgroup','data','datalist','dd','del','details','dfn','dialog','div','dl','dt','em','embed','fieldset','figcaption','figure','footer','form','h1','h2','h3','h4','h5','h6','head','header','hr','html','i','iframe','img','input','ins','kbd','label','legend','li','link','main','map','mark','meta','meter','nav','noscript','object','ol','optgroup','option','output','p','param','picture','pre','progress','q','rb','rp','rt','rtc','ruby','s','samp','script','section','select','slot','small','source','span','strong','style','sub','summary','sup','table','tbody','td','template','textarea','tfoot','th','thead','time','title','tr','track','u','ul','var','video','wbr'
  ];
  const disallowedTags = ['script', 'object', 'embed', 'style', 'link', 'base'];
  const allowedTags = allHtmlTags.filter(tag => !disallowedTags.includes(tag));
  res.json({ allowedTags });
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
  console.log(`DOM Inspector JS Backend running on port ${PORT}`);
});

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
});

// Helper for consistent error responses
function errorResponse(res, message, code) {
  return res.status(code).json({ error: message, code });
} 
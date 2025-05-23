const { JSDOM } = require('jsdom');

const LOCATOR_SCORES = {
  id: 100,
  name_type: 95,
  label: 90,
  'aria-label': 85,
  role: 85,
  class: 80,
  data: 75,
  name: 70,
  placeholder: 60,
  title: 60,
  value: 60,
  type: 60,
  text: 50,
  css: 25,
  xpath: 30,
};

function isUnstableClass(cls) {
  // Penalize classes that look auto-generated
  return /^(Mui|ant-|[A-Za-z0-9]{8,})/.test(cls);
}

function getAllXPaths(el, doc) {
  const xpaths = [];
  const tag = el.tag;
  // 1. By ID
  if (el.id) xpaths.push({ xpath: `//*[@id='${el.id}']`, reason: 'id' });
  // 2. By text (exact)
  if (el.text && el.text.length > 0) {
    xpaths.push({ xpath: `//${tag}[normalize-space(text())='${el.text}']`, reason: 'text' });
  }
  // 3. By single attribute
  for (const attr of Object.keys(el.attributes || {})) {
    if ([
      'id', 'class', 'name', 'type', 'role', 'aria-label', 'placeholder', 'title', 'value',
    ].includes(attr)) {
      xpaths.push({ xpath: `//${tag}[@${attr}='${el.attributes[attr]}']`, reason: `@${attr}` });
    }
  }
  // 4. By two attributes
  const attrs = Object.keys(el.attributes || {}).filter(a => [
    'id', 'class', 'name', 'type', 'role', 'aria-label',
  ].includes(a));
  if (attrs.length > 1) {
    for (let i = 0; i < attrs.length; i++) {
      for (let j = i + 1; j < attrs.length; j++) {
        xpaths.push({ xpath: `//${tag}[@${attrs[i]}='${el.attributes[attrs[i]]}' and @${attrs[j]}='${el.attributes[attrs[j]]}']`, reason: `@${attrs[i]}+@${attrs[j]}` });
      }
    }
  }
  // 5. By contains/starts-with
  for (const attr of attrs) {
    const val = el.attributes[attr];
    if (val && val.length > 4) {
      xpaths.push({ xpath: `//${tag}[contains(@${attr}, '${val.substring(0, 5)}')]`, reason: `contains(@${attr})` });
      xpaths.push({ xpath: `//${tag}[starts-with(@${attr}, '${val.substring(0, 5)}')]`, reason: `starts-with(@${attr})` });
    }
  }
  // 6. By parent context
  if (el.parent && el.parent.id) {
    xpaths.push({ xpath: `//*[@id='${el.parent.id}']//${tag}`, reason: 'parent id' });
  }
  // 7. By nth-child
  if (el.parent) {
    const siblings = el.parent.children.filter(e => e.tag === tag);
    const idx = siblings.indexOf(el) + 1;
    if (idx > 0) xpaths.push({ xpath: `//${tag}[${idx}]`, reason: 'nth-child' });
  }
  // 8. By label context (for form elements)
  if (["input", "select", "textarea"].includes(tag)) {
    let labelText = '';
    if (el.parent && el.parent.tag === 'label') {
      labelText = el.parent.text;
    }
    if (!labelText && el.id && doc) {
      const label = Array.from(doc.querySelectorAll('label')).find(l => l.getAttribute('for') === el.id);
      if (label) labelText = label.textContent.trim();
    }
    if (labelText) xpaths.push({ xpath: `//label[normalize-space(text())='${labelText}']/following-sibling::${tag}`, reason: 'label' });
  }
  return xpaths;
}

function getAllCssSelectors(el, doc) {
  const selectors = [];
  const tag = el.tag;
  // 1. By ID
  if (el.id) selectors.push({ selector: `#${el.id}`, reason: 'id' });
  // 2. By class
  if (el.class && typeof el.class === 'string') {
    const classes = el.class.split(/\s+/).filter(Boolean);
    if (classes.length) selectors.push({ selector: `${tag}.${classes.join('.')}`, reason: 'class', unstable: classes.some(isUnstableClass) });
  }
  // 3. By single attribute
  for (const attr of Object.keys(el.attributes || {})) {
    if ([
      'name', 'type', 'role', 'aria-label', 'placeholder', 'title', 'value',
    ].includes(attr)) {
      selectors.push({ selector: `${tag}[${attr}='${el.attributes[attr]}']`, reason: `@${attr}` });
    }
  }
  // 4. By two attributes
  const attrs = Object.keys(el.attributes || {}).filter(a => [
    'name', 'type', 'role', 'aria-label',
  ].includes(a));
  if (attrs.length > 1) {
    for (let i = 0; i < attrs.length; i++) {
      for (let j = i + 1; j < attrs.length; j++) {
        selectors.push({ selector: `${tag}[${attrs[i]}='${el.attributes[attrs[i]]}'][${attrs[j]}='${el.attributes[attrs[j]]}']`, reason: `@${attrs[i]}+@${attrs[j]}` });
      }
    }
  }
  // 5. By contains/starts-with
  for (const attr of attrs) {
    const val = el.attributes[attr];
    if (val && val.length > 4) {
      selectors.push({ selector: `${tag}[${attr}*='${val.substring(0, 5)}']`, reason: `contains(@${attr})` });
      selectors.push({ selector: `${tag}[${attr}^='${val.substring(0, 5)}']`, reason: `starts-with(@${attr})` });
    }
  }
  // 6. By parent context
  if (el.parent && el.parent.id) {
    selectors.push({ selector: `#${el.parent.id} > ${tag}`, reason: 'parent id' });
  }
  // 7. By nth-child
  if (el.parent) {
    const siblings = el.parent.children.filter(e => e.tag === tag);
    const idx = siblings.indexOf(el) + 1;
    if (idx > 0) selectors.push({ selector: `${tag}:nth-of-type(${idx})`, reason: 'nth-child' });
  }
  // 8. By label context (for form elements)
  if (["input", "select", "textarea"].includes(tag)) {
    let labelText = '';
    if (el.parent && el.parent.tag === 'label') {
      labelText = el.parent.text;
    }
    if (!labelText && el.id && doc) {
      const label = Array.from(doc.querySelectorAll('label')).find(l => l.getAttribute('for') === el.id);
      if (label) labelText = label.textContent.trim();
    }
    if (labelText) selectors.push({ selector: `label:contains('${labelText}') + ${tag}`, reason: 'label' });
  }
  return selectors;
}

function isXPathUnique(xpath, allElements, doc) {
  try {
    const result = doc.evaluate(xpath, doc, null, 7, null); // XPathResult.ORDERED_NODE_SNAPSHOT_TYPE = 7
    return result.snapshotLength === 1;
  } catch {
    return false;
  }
}

function isCssUnique(selector, allElements, doc) {
  try {
    return doc.querySelectorAll(selector).length === 1;
  } catch {
    return false;
  }
}

function extractLocators({ dom, elements, tags }) {
  let elementList = [];
  let doc = null;
  if (dom) {
    const jsdom = new JSDOM(dom);
    doc = jsdom.window.document;
    const allNodes = Array.from(doc.querySelectorAll('*'));
    // Map from DOM node to element object
    const nodeToElement = new Map();
    elementList = allNodes.map(el => {
      const obj = {
        tag: el.tagName.toLowerCase(),
        id: el.id || '',
        name: el.getAttribute('name') || '',
        type: el.getAttribute('type') || '',
        class: el.className || '',
        text: (el.innerText || '').trim(),
        value: el.value || '',
        aria_label: el.getAttribute('aria-label') || '',
        role: el.getAttribute('role') || '',
        attributes: Object.fromEntries(Array.from(el.attributes).map(a => [a.name, a.value])),
        visible: !!(el.offsetParent !== null),
        parent: null, // will be set below
        children: [], // will be set below
      };
      nodeToElement.set(el, obj);
      return obj;
    });
    // Set parent/children relationships for all elements
    allNodes.forEach((el, idx) => {
      const obj = elementList[idx];
      if (el.parentElement && nodeToElement.has(el.parentElement)) {
        obj.parent = nodeToElement.get(el.parentElement);
      }
      obj.children = Array.from(el.children)
        .filter(child => nodeToElement.has(child))
        .map(child => nodeToElement.get(child));
    });
  } else if (elements) {
    elementList = elements;
  }
  // Helper to check uniqueness in the list for basic locators
  function isUnique(type, value) {
    return elementList.filter(e => {
      if (type === 'id') return e.id && `#${e.id}` === value;
      if (type === 'class') return e.class && typeof e.class === 'string' && ('.' + e.class.split(/\s+/).join('.')) === value;
      if (type === 'name') return e.name && `[name="${e.name}"]` === value;
      if (type === 'name_type') return e.name && e.type && `[name="${e.name}"][type="${e.type}"]` === value;
      if (type === 'aria-label') return e.aria_label && `[aria-label="${e.aria_label}"]` === value;
      if (type === 'role') return e.role && `[role="${e.role}"]` === value;
      if (type === 'placeholder') return e.attributes && e.attributes.placeholder && `[placeholder="${e.attributes.placeholder}"]` === value;
      if (type === 'title') return e.attributes && e.attributes.title && `[title="${e.attributes.title}"]` === value;
      if (type === 'value') return e.value && `[value="${e.value}"]` === value;
      if (type === 'type') return e.type && `[type="${e.type}"]` === value;
      if (type === 'text') return e.text && e.text === value;
      if (type === 'data') return Object.entries(e.attributes || {}).some(([k, v]) => k.startsWith('data-') && `[${k}="${v}"]` === value);
      return false;
    }).length === 1;
  }
  // Locator extraction per element
  const results = elementList.map((el, idx) => {
    // Compute parent_index and children_indices
    let parent_index = null;
    let parent_tag = null;
    if (el.parent) {
      parent_index = elementList.indexOf(el.parent);
      parent_tag = el.parent.tag;
      if (parent_index === -1) parent_index = null;
    }
    const children_indices = (el.children || []).map(child => elementList.indexOf(child)).filter(i => i !== -1);
    const children_tags = (el.children || []).map(child => child.tag);
    // --- More metadata ---
    let position = null;
    let custom_attributes = {};
    if (doc) {
      const node = doc.querySelectorAll('*')[idx];
      // jsdom does not support layout, but we can provide bounding rect if available
      if (node && typeof node.getBoundingClientRect === 'function') {
        const rect = node.getBoundingClientRect();
        position = { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
      }
      // Collect all data-* attributes
      custom_attributes = {};
      for (const attr of Array.from(node.attributes || [])) {
        if (attr.name.startsWith('data-')) {
          custom_attributes[attr.name] = attr.value;
        }
      }
    }
    const locators = [];
    if (el.id) locators.push({ type: 'id', value: `#${el.id}` });
    if (el.class && typeof el.class === 'string') locators.push({ type: 'class', value: '.' + el.class.split(/\s+/).join('.') });
    if (el.name) locators.push({ type: 'name', value: `[name="${el.name}"]` });
    if (el.name && el.type) locators.push({ type: 'name_type', value: `[name="${el.name}"][type="${el.type}"]` });
    if (el.aria_label) locators.push({ type: 'aria-label', value: `[aria-label="${el.aria_label}"]` });
    if (el.role) locators.push({ type: 'role', value: `[role="${el.role}"]` });
    if (el.attributes && el.attributes.placeholder) locators.push({ type: 'placeholder', value: `[placeholder="${el.attributes.placeholder}"]` });
    if (el.attributes && el.attributes.title) locators.push({ type: 'title', value: `[title="${el.attributes.title}"]` });
    if (el.value) locators.push({ type: 'value', value: `[value="${el.value}"]` });
    if (el.type) locators.push({ type: 'type', value: `[type="${el.type}"]` });
    if (el.text) locators.push({ type: 'text', value: el.text });
    if (el.attributes) {
      for (const [k, v] of Object.entries(el.attributes)) {
        if (k.startsWith('data-')) locators.push({ type: 'data', value: `[${k}="${v}"]` });
      }
    }
    // --- Advanced relative XPath/CSS logic ---
    let relative_xpath = null;
    let relative_css = null;
    let best_locator = null;
    let xpathLocators = [];
    let cssLocators = [];
    if (doc) {
      xpathLocators = getAllXPaths(el, doc).map(x => ({
        type: 'xpath',
        value: x.xpath,
        unique: isXPathUnique(x.xpath, elementList, doc),
        score: LOCATOR_SCORES['xpath'],
        reason: x.reason,
      }));
      cssLocators = getAllCssSelectors(el, doc).map(s => ({
        type: 'css',
        value: s.selector,
        unique: isCssUnique(s.selector, elementList, doc),
        score: s.unstable ? 10 : LOCATOR_SCORES['css'],
        reason: s.reason,
      }));
      const uniqueXPath = xpathLocators.find(x => x.unique);
      const uniqueCss = cssLocators.find(s => s.unique);
      if (uniqueXPath) relative_xpath = uniqueXPath.value;
      if (uniqueCss) relative_css = uniqueCss.value;
    }
    // Uniqueness and scoring for basic locators
    const locatorsWithMeta = locators.map(l => ({
      ...l,
      unique: l.unique !== undefined ? l.unique : isUnique(l.type, l.value),
      score: l.score || LOCATOR_SCORES[l.type] || 10,
    }));
    // Best locator selection
    const uniqueLocators = locatorsWithMeta.filter(l => l.unique);
    if (uniqueLocators.length > 0) {
      best_locator = uniqueLocators.reduce((a, b) => (a.score > b.score ? a : b));
    } else if (locatorsWithMeta.length > 0) {
      best_locator = locatorsWithMeta.reduce((a, b) => (a.score > b.score ? a : b));
    }
    return {
      ...el,
      parent_index,
      parent_tag,
      children_indices,
      children_tags,
      position,
      custom_attributes,
      locators: locatorsWithMeta,
      best_locator,
      relative_xpath,
      relative_css,
      index: idx,
    };
  });
  // Only filter by tags at the end, if provided
  if (tags && tags.length > 0) {
    return results.filter(el => tags.includes(el.tag));
  }
  return results;
}

module.exports = { extractLocators }; 
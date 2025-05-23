const { Parser: Json2csvParser } = require('json2csv');
const js2xmlparser = require('js2xmlparser');

function exportResults({ elements, format }) {
  if (format === 'csv') {
    const parser = new Json2csvParser();
    return parser.parse(elements || []);
  } else if (format === 'xml') {
    return js2xmlparser.parse('elements', elements || []);
  } else if (format === 'selenium') {
    // Placeholder: generate Python Selenium code for each best locator
    return (elements || []).map(el => `driver.find_element(By.${el.best_locator?.type?.toUpperCase() || 'CSS_SELECTOR'}, "${el.best_locator?.value}")`).join('\n');
  } else if (format === 'playwright') {
    // Placeholder: generate JS Playwright code for each best locator
    return (elements || []).map(el => `await page.locator('${el.best_locator?.value}').click();`).join('\n');
  } else {
    return JSON.stringify(elements || []);
  }
}

module.exports = { exportResults }; 
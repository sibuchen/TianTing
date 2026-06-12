const fs = require('fs');

function htmlToJsx(html) {
    let jsx = html.replace(/class=/g, 'className=')
                  .replace(/for=/g, 'htmlFor=')
                  .replace(/<!--[\s\S]*?-->/g, '') // remove comments
                  // self-closing tags
                  .replace(/<input([^>]*[^\/])>/g, '<input$1 />')
                  .replace(/<img([^>]*[^\/])>/g, '<img$1 />')
                  .replace(/<br>/g, '<br />')
                  .replace(/<hr([^>]*[^\/])>/g, '<hr$1 />')
                  .replace(/disabled=""/g, 'disabled')
                  .replace(/style="([^"]*)"/g, (match, styleString) => {
                      return `style={{ ${styleString.split(';').filter(s=>s.trim()).map(s => {
                          let [key, val] = s.split(':');
                          key = key.trim().replace(/-([a-z])/g, g => g[1].toUpperCase());
                          return `${key}: '${val.trim()}'`;
                      }).join(', ')} }}`;
                  });
    return jsx;
}

const htmlFile = 'd:\\Learning\\CodeData\\XM\\13_TianTing\\TianTing_frontend2\\HTML原型\\Skills.html';
const outFile = 'd:\\Learning\\CodeData\\XM\\13_TianTing\\TianTing_frontend2\\tianting-frontend\\src\\app\\(admin)\\skills\\page.tsx';

const content = fs.readFileSync(htmlFile, 'utf8');

// Extract just the Page Content part
const pageContentMatch = content.match(/<!-- Page Content -->\s*(<div[\s\S]*?)<\/main>/);

if (pageContentMatch) {
    let jsxContent = htmlToJsx(pageContentMatch[1]);
    
    const finalContent = `'use client';\n\nimport React from 'react';\n\nexport default function SkillsPage() {\n  return (\n    <>\n${jsxContent}\n    </>\n  );\n}\n`;
    fs.writeFileSync(outFile, finalContent);
    console.log('Processed Skills page');
} else {
    console.log('Failed to find Page Content');
}

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
                  .replace(/style="([^"]*)"/g, (match, styleString) => {
                      // super simple style conversion for specific ones in the HTML
                      let styleObj = '{' + styleString.split(';').filter(s => s.trim()).map(s => {
                          let [key, value] = s.split(':');
                          key = key.trim().replace(/-([a-z])/g, g => g[1].toUpperCase());
                          return `${key}: '${value.trim()}'`;
                      }).join(', ') + '}';
                      return `style={{ ${styleString.split(';').filter(s=>s.trim()).map(s => {
                          let [key, val] = s.split(':');
                          key = key.trim().replace(/-([a-z])/g, g => g[1].toUpperCase());
                          return `${key}: '${val.trim()}'`;
                      }).join(', ')} }}`;
                  });
    return jsx;
}

const templates = [
    {
        htmlFile: 'd:\\Learning\\CodeData\\XM\\13_TianTing\\TianTing_frontend2\\HTML原型\\log in.html',
        outFile: 'd:\\Learning\\CodeData\\XM\\13_TianTing\\TianTing_frontend2\\tianting-frontend\\src\\app\\(auth)\\login\\page.tsx',
        regex: /<body[^>]*>([\s\S]*?)<\/body>/
    },
    {
        htmlFile: 'd:\\Learning\\CodeData\\XM\\13_TianTing\\TianTing_frontend2\\HTML原型\\register.html',
        outFile: 'd:\\Learning\\CodeData\\XM\\13_TianTing\\TianTing_frontend2\\tianting-frontend\\src\\app\\(auth)\\register\\page.tsx',
        regex: /<body[^>]*>([\s\S]*?)<\/body>/
    },
    {
        htmlFile: 'd:\\Learning\\CodeData\\XM\\13_TianTing\\TianTing_frontend2\\HTML原型\\forgot password.html',
        outFile: 'd:\\Learning\\CodeData\\XM\\13_TianTing\\TianTing_frontend2\\tianting-frontend\\src\\app\\(auth)\\forgot-password\\page.tsx',
        regex: /<body[^>]*>([\s\S]*?)<\/body>/
    }
];

templates.forEach(t => {
    const content = fs.readFileSync(t.htmlFile, 'utf8');
    let match = content.match(t.regex);
    if (match) {
        let jsxContent = htmlToJsx(match[1]);
        
        let bodyMatch = content.match(/<body class="([^"]+)"/);
        let wrapperClass = bodyMatch ? bodyMatch[1] : '';
        
        // Wrap with a component
        const finalContent = `'use client';\n\nimport Link from 'next/link';\n\nexport default function Page() {\n  return (\n    <div className="${wrapperClass}">\n${jsxContent}\n    </div>\n  );\n}\n`;
        fs.writeFileSync(t.outFile, finalContent);
        console.log('Processed', t.outFile);
    }
});


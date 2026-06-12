const fs = require('fs');
const path = require('path');

const htmlPath = 'd:\\Learning\\CodeData\\XM\\13_TianTing\\TianTing_frontend2\\HTML原型\\Skills.html';
const htmlContent = fs.readFileSync(htmlPath, 'utf8');

// Extract the tailwind config json
const match = htmlContent.match(/tailwind\.config\s*=\s*(\{[\s\S]*?\})\s*<\/script>/);
if (match) {
    // we need to parse this JS object. It's not strict JSON, but it looks like standard JSON in this file
    const configStr = match[1].replace(/\\"/g, '"');
    
    // Evaluate the object
    let config;
    eval('config = ' + configStr);
    
    const colors = config.theme.extend.colors;
    
    let themeCss = '\n@theme {\n';
    for (const [key, value] of Object.entries(colors)) {
        themeCss += `  --color-${key}: ${value};\n`;
    }
    
    // Also add fonts
    themeCss += `  --font-body-md: "Inter", sans-serif;\n`;
    themeCss += `  --font-label-md: "Inter", sans-serif;\n`;
    themeCss += `  --font-h1: "Inter", sans-serif;\n`;
    themeCss += `  --font-h2: "Inter", sans-serif;\n`;
    themeCss += `  --font-h3: "Inter", sans-serif;\n`;
    themeCss += `  --font-label-sm: "Inter", sans-serif;\n`;
    themeCss += `  --font-body-sm: "Inter", sans-serif;\n`;
    themeCss += `  --font-code: "JetBrains Mono", monospace;\n`;
    
    themeCss += '}\n';
    
    const globalsPath = 'd:\\Learning\\CodeData\\XM\\13_TianTing\\TianTing_frontend2\\tianting-frontend\\src\\app\\globals.css';
    let globalsContent = fs.readFileSync(globalsPath, 'utf8');
    globalsContent += themeCss;
    fs.writeFileSync(globalsPath, globalsContent);
    console.log('Successfully updated globals.css');
} else {
    console.log('Could not find tailwind config in HTML');
}

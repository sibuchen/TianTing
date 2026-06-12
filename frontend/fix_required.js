const fs = require('fs');

const files = [
    'src/app/(auth)/login/page.tsx',
    'src/app/(auth)/register/page.tsx',
    'src/app/(auth)/forgot-password/page.tsx',
    'src/app/(admin)/skills/page.tsx'
];

files.forEach(f => {
    try {
        let content = fs.readFileSync(f, 'utf8');
        content = content.replace(/required=""/g, 'required');
        fs.writeFileSync(f, content);
        console.log('Fixed', f);
    } catch(e) {
        console.log('Error', f, e.message);
    }
});

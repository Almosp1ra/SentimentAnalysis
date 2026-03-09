export function InitializeTabs()
{
    document.querySelectorAll('#tabs .tab')
        .forEach(t => t.addEventListener('click', () => loadPanel(t.dataset.panel)));
}

export async function loadPanel(name)
{ 
    const main = document.getElementById('main');
    try {
        // const resp = await fetch(`/static/html/${name}.html`);
        const resp = await fetch(`../static/html/${name}.html`);
        const html = await resp.text();
        main.innerHTML = html;
        try {
            await import(`./${name}.js`).then(m => {
                if(m.Initialize)
                    m.Initialize();
            });
        }
        catch(e) {
            ;
        }
    }
    catch(e) {
        main.innerHTML='<div class="p-6 bg-white">加载错误</div>';
    }
}
// Builds the command doc card grids from a JSON entries file.
// JSON shape: [{ section, source, commands: [{ name, img, restricted, params, description }] }]

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function buildCommandCard(cmd) {
    const badge = cmd.restricted ? ' <span class="badge badge-danger">Bot Owner Only</span>' : '';
    return `
            <div class="col-md-4 col-12">
            <h5 class="mt-0 mb-1">${escapeHtml(cmd.name)}${badge}</h5>
            <img src="${cmd.img || ''}" alt="${escapeHtml(cmd.name)} preview" class="img-fluid mb-2">
            <p><strong>Parameters:</strong> ${cmd.params || 'none'}</p>
            <p>${cmd.description || ''}</p>
            </div>`;
}

function buildSection(section) {
    const cardsHtml = (section.commands || []).map(buildCommandCard).join('\n');
    return `
        <div class="row">
            <div class="col-12 text-center">
            <h2>${escapeHtml(section.section)}</h2>
            <p>From ${section.source || ''}</p>
            </div>
            ${cardsHtml}
        </div>
        <hr>`;
}

async function renderCommands(containerId, jsonPath) {
    const container = document.getElementById(containerId);
    if (!container) return;

    let sections = [];
    try {
        const res = await fetch(jsonPath);
        sections = await res.json();
    } catch (err) {
        console.error(`renderCommands: failed to load ${jsonPath}`, err);
    }

    if (!sections.length) {
        container.innerHTML = '<div class="row"><div class="col-12 text-center"><p>Couldn\'t load command list.</p></div></div>';
        return;
    }

    container.innerHTML = sections.map(buildSection).join('\n');
}

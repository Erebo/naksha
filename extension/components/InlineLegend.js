/**
 * Inline Legend & Layer Styling Utilities
 * Renders an inline 1-2 row legend directly beneath the map (replacing the popover).
 * Interactive:
 * - Click toggles the layer visibility on/off.
 * - Hover dims other layers to 30% and highlights the hovered layer.
 */

function renderInlineLegend(container, layersData, onToggle, onHover) {
  if (!container) return;

  const isEn = (typeof currentLang !== 'undefined' && currentLang === 'en');

  // Definition of the 5 layers with distinct styles & swatches
  const layerDefs = [
    {
      type: 'ancestral_footprint',
      name: isEn ? 'Ancestral CS 88' : 'সিএস ৮৮ পৈত্রিক',
      color: '#A78BFA',
      dash: 'dashed-violet',
      area: '18.00',
    },
    {
      type: 'deed_claim',
      name: isEn ? 'Deed Claim' : 'দলিল দাবি',
      color: '#FB923C',
      dash: 'solid-orange',
      area: '6.00',
    },
    {
      type: 'ground_truth',
      name: isEn ? 'DLRS Truth' : 'ডিএলআরএস জরিপ',
      color: '#3B82F6',
      dash: 'solid-blue',
      area: '5.10',
    },
    {
      type: 'restricted_khas',
      name: isEn ? 'Khas Canal' : 'খাস নিষ্কাশন খাল',
      color: '#22D3EE',
      dash: 'wave-cyan',
      area: '4.48',
    },
    {
      type: 'conflict_zone',
      name: isEn ? 'Conflict (0.9 dec)' : 'বিরোধপূর্ণ (০.৯ শতক)',
      color: '#F43F5E',
      dash: 'hatch-red',
      area: '0.90',
    },
  ];

  container.innerHTML = `
    <div class="inline-legend-row" id="inline-legend-row">
      ${layerDefs.map(l => {
        const isChecked = state.layerVisibility[l.type] !== false;
        const areaStr = formatNumber(parseFloat(l.area)) + ' ' + (isEn ? 'dec' : 'শতক');

        return `
          <label class="legend-chip ${isChecked ? 'active' : 'inactive'}" 
                 data-layer="${l.type}" 
                 title="${isEn ? 'Click to toggle, hover to highlight' : 'ক্লিক করে প্রদর্শন বন্ধ/চালু করুন'}">
            <input type="checkbox" ${isChecked ? 'checked' : ''} class="leg-chk" data-layer="${l.type}">
            <span class="leg-swatch swatch-${l.dash}"></span>
            <span class="leg-label">${l.name}</span>
            <span class="leg-area num">${areaStr}</span>
          </label>
        `;
      }).join('')}
    </div>
  `;

  // Attach interactive toggle and hover highlighting
  container.querySelectorAll('.legend-chip').forEach(chip => {
    const type = chip.dataset.layer;
    const chk = chip.querySelector('input');

    // Toggle on change
    chk.addEventListener('change', (e) => {
      e.stopPropagation();
      const checked = chk.checked;
      chip.classList.toggle('active', checked);
      chip.classList.toggle('inactive', !checked);
      if (onToggle) onToggle(type, checked);
    });

    // Hover effect: highlight hovered layer, dim other layers to 30%
    chip.addEventListener('mouseenter', () => {
      if (onHover) onHover(type, true);
    });
    chip.addEventListener('mouseleave', () => {
      if (onHover) onHover(type, false);
    });
  });
}

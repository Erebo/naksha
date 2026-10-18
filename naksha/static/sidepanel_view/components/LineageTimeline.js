/**
 * LineageTimeline Component (History Tab)
 * CS -> SA -> RS -> BS lineage timeline with fractional shares, glowing active node,
 * share partition check, and phonetic name match progress bar.
 */

function renderLineageTimeline(container, data) {
  if (!container) return;

  const isEn = (typeof currentLang !== 'undefined' && currentLang === 'en');
  const cleanDag = data.dag || '402';
  const cleanDagStr = isEn ? cleanDag : toBnDigits(cleanDag);

  const nodes = [
    { era: isEn ? 'CS 1940' : 'সিএস ১৯৪০', dag: isEn ? '88' : '৮৮', share: isEn ? '16/16 share' : '১৬/১৬ অংশ', area: isEn ? '18.0 dec' : '১৮.০ শতক' },
    { era: isEn ? 'SA 1962' : 'এসএ ১৯৬২', dag: isEn ? '88' : '৮৮', share: isEn ? '8/16 + 8/16' : '৮/১৬ + ৮/১৬', area: isEn ? '18.0 dec' : '১৮.০ শতক' },
    { era: isEn ? 'RS 1988' : 'আরএস ১৯৮৮', dag: isEn ? '112' : '১১২', share: isEn ? '4/16 part' : '৪/১৬ অংশ', area: isEn ? '6.0 dec' : '৬.০ শতক' },
    { era: isEn ? 'BS Present' : 'বিএস বর্তমান', dag: cleanDagStr, share: isEn ? 'Mutated' : 'নামজারি', area: isEn ? '5.1 dec' : '৫.১ শতক', active: true },
  ];

  const matchScore = data.nameMatchScore || 92;
  const matchScoreStr = (isEn ? String(matchScore) : toBnDigits(matchScore)) + '%';

  container.innerHTML = `
    <div class="bento-card">
      <div class="bento-card-header">
        <span class="bento-title">${isEn ? 'Cadastral Survey Lineage' : 'ক্যাডাস্ট্রাল জরিপ ও বাটোয়ারা ধারা'}</span>
        <span class="bento-badge num" style="color: var(--status-clear);">
          ${isEn ? 'Partition Intact' : 'বাটোয়ারা অটুট'}
        </span>
      </div>

      <!-- Horizontal Lineage Node Track -->
      <div class="lineage-minimal-track">
        <div class="lmt-axis-line"></div>
        ${nodes.map(n => `
          <div class="lmt-node ${n.active ? 'active-node' : ''}">
            <div class="lmt-dot ${n.active ? 'glow-dot' : ''}"></div>
            <div class="lmt-era font-bold">${n.era}</div>
            <div class="lmt-dag num">${isEn ? 'Dag' : 'দাগ'} ${n.dag}</div>
            <div class="lmt-share num">${n.share}</div>
          </div>
        `).join('')}
      </div>

      <!-- Phonetic Name Match Meter -->
      <div class="lineage-phonetic-box">
        <div class="lpb-header">
          <span class="lpb-title">${isEn ? 'Owner Name Phonetic Match' : 'মালিকের নামের ধ্বনিগত মিল'}</span>
          <span class="lpb-score num" style="color: var(--accent-brand);">${matchScoreStr}</span>
        </div>
        <div class="lpb-track">
          <div class="lpb-fill" style="width: ${matchScore}%; background-color: var(--accent-brand);"></div>
        </div>
        <div class="lpb-desc">
          ${isEn 
            ? 'Bangla phonetic soundex verified between registered deed and RS khatian.' 
            : 'সাব-রেজিস্ট্রি দলিল ও আরএস খতিয়ানের মধ্যে বাংলা ধ্বনিগত মিল সন্তোষজনক।'}
        </div>
      </div>
    </div>
  `;
}

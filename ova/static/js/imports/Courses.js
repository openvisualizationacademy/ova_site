document.addEventListener('DOMContentLoaded', function() {
  const filters = document.querySelector('.filters');
  const cards = document.querySelectorAll('.course');

  // 1. Define your color palette (6 colors, will cycle if more tags)
  const colors = [
    "#fb7d07", // red
    "#ffae34", // orange
    "#4e79a7", // blue
    "#59a14f", // green
    "#af7aa1", // purple
    "#ff9da7", // pink
  ];

  // 2. Collect all unique tags from the filter bar
  const tagSet = new Set();
  document.querySelectorAll('.filters label[data-tag]').forEach(label => {
    tagSet.add(label.getAttribute('data-tag'));
  });
  const allTags = Array.from(tagSet).sort();

  // 3. Build tag -> color mapping
  const tagColorMap = {};
  allTags.forEach((tag, i) => {
    tagColorMap[tag] = colors[i % colors.length];
  });

  // 4. Apply colors to filter labels
  document.querySelectorAll('.filters label[data-tag]').forEach(label => {
    const tag = label.getAttribute('data-tag');
    if (tagColorMap[tag]) {
      label.style.color = tagColorMap[tag];
    }
  });

  // 5. Apply colors to tags on cards
  document.querySelectorAll('.cards .tag[data-tag]').forEach(span => {
    const tag = span.getAttribute('data-tag');
    if (tagColorMap[tag]) {
      span.style.color = tagColorMap[tag];
    }
  });

  filters.addEventListener('change', function() {
    const tag = filters.querySelector('input[name="tag"]:checked').value;
    cards.forEach(card => {
      const tags = card.getAttribute('data-tags').split(',');
      if (tag === "all" || tags.includes(tag)) {
        card.style.display = '';
      } else {
        card.style.display = 'none';
      }
    });
  });
});


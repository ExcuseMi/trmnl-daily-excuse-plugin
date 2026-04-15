function transform(input) {
  var all = Array.isArray(input.data) ? input.data : [];
  if (all.length === 0) {
    return { reasons: [
      { text: "Computer says 'No'!", index: 1, total: 1 },
      { text: "Absolutely not.",     index: 2, total: 2 },
      { text: "Hard pass.",          index: 3, total: 3 },
      { text: "Not going to happen.", index: 4, total: 4 }
    ]};
  }
  // Fisher-Yates shuffle on index-tagged items, take 4
  var pool = all.map(function(text, i) { return { text: text, index: i + 1, total: all.length }; });
  for (var i = pool.length - 1; i > 0; i--) {
    var j = Math.floor(Math.random() * (i + 1));
    var tmp = pool[i]; pool[i] = pool[j]; pool[j] = tmp;
  }
  return { reasons: pool.slice(0, 4) };
}

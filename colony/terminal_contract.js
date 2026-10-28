(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./services.js'));
  else root.ColonyTerminalContract = factory(root.ColonyServices);
})(globalThis, function (services) {
  'use strict';
  const no = cause => ({ seal: 'NO_DATA', cause: cause.length <= 120 ? cause : 'cause_too_large' });
  function assess(node, card, terminal, rows, catalog, query) {
    if (node !== 'atlantis' && node !== 'risen') return no('unknown_node');
    if (!card || card.verified !== true) return no(card && typeof card.cause === 'string' && card.cause.trim() ? card.cause : 'card_unverified');
    if (typeof card.cause !== 'string' || !card.cause.trim()) return no('card_unverified');
    if (!terminal || terminal.reachable !== true) return no(terminal && typeof terminal.cause === 'string' && terminal.cause.trim() ? terminal.cause : 'terminal_unmeasured');
    if (typeof terminal.cause !== 'string' || !terminal.cause.trim()) return no('terminal_unmeasured');
    if (!query || query.node !== node) return no('node_mismatch');
    return services.resolve(rows, catalog, query);
  }
  return { assess };
});

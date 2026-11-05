// Workspace object-card geometry shared by native and browser batch rows.
export const fonts = Object.freeze({micro:11,caption:11,label:12,body:13,bodyLarge:14,title:16});
export const catalog = Object.freeze({height:88, preview:48, padding:12, leading:18});
export const queue = Object.freeze({episodeHeight:88, shotHeight:80, preview:44, indent:24});
export const card = Object.freeze({inset:4, railWidth:4, railMargin:12, gap:3});
export function cssMetrics() {
    return {'--row-font-size':fonts.body+'px','--row-secondary-font-size':fonts.label+'px','--catalog-row-height':catalog.height+'px','--catalog-preview':catalog.preview+'px',
            '--episode-row-height':queue.episodeHeight+'px','--shot-row-height':queue.shotHeight+'px',
            '--queue-preview':queue.preview+'px','--row-indent':queue.indent+'px',
            '--card-inset':card.inset+'px','--card-gap':card.gap+'px',
            '--card-rail':card.railWidth+'px','--card-rail-margin':card.railMargin+'px'};
}

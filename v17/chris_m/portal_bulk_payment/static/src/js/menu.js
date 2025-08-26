/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import animations from "@website/js/content/snippets.animation";

const BaseAnimatedLoader = animations.Animation.extend({
    disabledInEditableMode: false, 
    init: function () {
        this._super(...arguments); 
        this.scrolledPoint = 0; 
    }, 
    start: function () {
        this._transitionCount = 0;
        this.$el.on('odoo-transitionstart.BaseAnimatedHeader', () => { 
            this._adaptToLoaderLoop(1);
        });
        this.$el.on('transitionend.BaseAnimatedHeader', () => this._adaptToLoaderLoop(-1)); 
        return this._super(...arguments);
    }, 
    _adaptToLoaderLoop: function (addCount = 0) { 

        this._transitionCount += addCount;
        this._transitionCount = Math.max(0, this._transitionCount);

        if (this._transitionCount > 0) {
            window.requestAnimationFrame(() => this._adaptToLoaderLoop());
            if (addCount !== 0) {
                clearTimeout(this._changeLoopTimer);
                this._changeLoopTimer = setTimeout(() => {
                    this._adaptToLoaderLoop(-this._transitionCount);
                }, 500);
            }
        } else {
            clearTimeout(this._changeLoopTimer); 
            $('#overlay-loadar').hide(); 
        }
    },
}); 
publicWidget.registry.WebLoader = BaseAnimatedLoader.extend({
    selector: 'header.o_header_standard:not(.o_header_sidebar)',
    init: function () {
        this._super(...arguments);
        this.scrolledPoint = 300;
    },
    start: function () {
        return this._super.apply(this, arguments);
    },
    destroy() {
        this._super(...arguments);
    },
});
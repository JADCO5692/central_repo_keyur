/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import publicWidget from "@web/legacy/js/public/public_widget"; 

publicWidget.registry.MenuWidget = publicWidget.Widget.extend({
    selector: 'header#top',
    events: {
        'mouseenter a.nav-link':'_onHover'
    },
    _onHover:function(ev){
        let parent = $(ev.currentTarget).parents('.s_mega_menu_boh_menu')
        let tabsContentMenu = $(ev.currentTarget).parents('.s_tabs_nav').find('a.nav-link')
        let tabsContent = parent.find('.s_tabs_content .tab-pane');
        let currentTabId =  $(ev.currentTarget).data('toggleid');
        let currentTabcontent = parent.find('.tab-pane'+currentTabId); 
        tabsContentMenu.each((e,i)=>{
            $(i).removeClass('active')
        });
        tabsContent.each((e,i)=>{
            $(i).removeClass('show active')
        })
        $(ev.currentTarget).addClass('active')
        currentTabcontent.addClass('active show');
    }

});
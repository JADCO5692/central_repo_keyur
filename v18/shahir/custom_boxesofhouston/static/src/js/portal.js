/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget"; 
import { _t } from "@web/core/l10n/translation";
import { renderToElement } from "@web/core/utils/render";
 
publicWidget.registry.PortalAttendence = publicWidget.Widget.extend({
    selector: '#o_portal_navbar_content',
    events:{
        'click li.filter': 'OnClickFilter',
        'click .btn-apply':'OnclickDateApply'
    }, 
    start:function(){
        this._super.apply(this, arguments); 
    },
    OnClickFilter:function(ev){
        let origin = window.location.origin;
        let filter = $(ev.currentTarget).data('filter');
        let url = $(ev.currentTarget).attr('href');
        if (filter != 'Custom'){
            window.location.href = origin + url;
        }else{
            $(ev.currentTarget).parents('.btn-group').find('button').html('Custom');
            let dateElem = renderToElement('custom_date_range');
            $(ev.currentTarget).parents('.nav').append(dateElem)
            this.trigger_up("widgets_start_request", { $target: this.$target });
        }
    },
    OnclickDateApply:function(ev){
        let $container = $(ev.currentTarget).parents('.dates-container');
        let origin = window.location.origin;
        let sdate = $container.find('.sdate')?.val();
        let edate = $container.find('.edate')?.val();
        window.location.href = origin + '/my/attendances?filterby=custom&sdate='+sdate+'&edate='+edate;
    }
}) 

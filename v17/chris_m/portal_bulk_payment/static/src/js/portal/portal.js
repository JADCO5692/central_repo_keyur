/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget"; 
import { _t } from '@web/core/l10n/translation';
import { renderToElement } from "@web/core/utils/render";
import { redirect } from "@web/core/utils/urls";

publicWidget.registry.PortalWrap = publicWidget.Widget.extend({
    selector: '.o_portal_wrap',
    events:{
        'click #o_sale_portal_paynow':'OnclickSignPay',
        'click .select_all':'OnclickSelectAll',
        'click #order_to_pay':'OnSelectOrder',
        'click #o_sale_portal_sign':'OnclickSign', 
        'click .order_accept':'OnClickAccept', 
    },
    init() {
        this._super(...arguments);
        this.rpc = this.bindService("rpc"); 
    }, 
    start: function () {
        var def = this._super.apply(this, arguments); 
        const hash = new URLSearchParams(window.location.search)
        if (hash.get("allow_payment") === "yes" && this.$("#o_sale_portal_paynow").length) {
            document.querySelector('#o_sale_portal_paynow').click() 
        } 
        return def;
    }, 
     
    OnclickSignPay: function (ev) { 
        var selected_lines = this.$el.find("input#order_to_pay:checked");
        if (selected_lines.length <= 0) { 
            ev.stopPropagation();
        }  
    },
    OnclickSign:function (ev) {
        var selected_lines = this.$el.find("input#order_to_pay:checked");
        if(!selected_lines.length) {
            ev.stopPropagation(); 
        }
        
    },
    OnclickSelectAll:async function (ev) { 
        var table = $(ev.currentTarget).parents('table');
        if(ev.currentTarget.checked){ 
            table.find('input#order_to_pay').prop('checked', true);
            $('#modalaccept').removeClass('d-none'); 
            var err = $('#modalaccept .o_sign_form').find('o_portal_sign_error_msg');
            if(err.length) {
                err.html('');
            }
            this.set_selected_count(ev);
        }else{
            table.find('input#order_to_pay').prop('checked', false);
            this.set_selected_count(ev);
        } 
        this._compute_payment(ev);
    },
    set_selected_count:function(ev){
        var table = $(ev.currentTarget).parents('table');
        var checked_ord = table.find('input#order_to_pay:checked');
        var is_signature = this.check_signature(checked_ord);
        if(checked_ord.length >= 1){
            if(is_signature){
                $('.sign-form-dialog').html(renderToElement('sign_dialog_btn'));
            }else{
                $('.sign-form-dialog').html(renderToElement('pay_dialog_btn'));
            } 
        }
        else{
            $('.sign-form-dialog').empty();
        }
        table.find('.selected_ord').html(checked_ord.length>=1 ? checked_ord.length:'');
    },
    check_signature:function(checked_ord){
        var is_signature = false;
        checked_ord.each((index, element) => {
            if($(element).data('sign')== 1){
                is_signature = true;
            } 
        });
        return is_signature
    },
    OnSelectOrder:async function (ev) {
        if(ev.currentTarget.checked){
            $('#modalaccept').removeClass('d-none'); 
        } 
        this.set_selected_count(ev);
        await this._compute_payment(ev);
    },
    _compute_payment:function(ev){
        var lines = $(ev.currentTarget).parents('table').find('input#order_to_pay:checked')
        var self = this;
        var order_ids = []; 
        lines.each(function(index, line){
            order_ids.push(parseInt(line.dataset.oid));
        }) 
        this.rpc("/compute/payable_amount", {
            order_ids: order_ids 
        }).then(function(res){
            $('.o_portal_wrap').find('#modalaccept .amount_to_pay').html(res.currency + res.total_amount);
            if (res.total_amount > 0 ){
                $('#modalaccept').removeClass('d-none');
            }
            else{
                $('#modalaccept').addClass('d-none');
            } 
        });   
    },
    OnClickAccept:async function(ev){
        var orders_list = $('.o_portal_wrap').find('.o_portal_my_doc_table #order_to_pay:checked');
        var order_ids = [];
        orders_list.each((index, element) => {
            order_ids.push($(element).data('oid'));
        }); 
        const data = await this.rpc('/accept/payment', { order_ids });
        if (data.force_refresh) {
            if (data.redirect_url) {
                redirect(data.redirect_url); 
            } else {
                window.location.reload();
            }
        }
    }
    
}); 

export default publicWidget.registry.PortalWrap;
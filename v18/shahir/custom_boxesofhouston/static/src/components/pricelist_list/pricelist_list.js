/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl"; 
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry"; 
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc"; 

function updateCartNavBar(data) {
    sessionStorage.setItem('website_sale_cart_quantity', data.cart_quantity);
    $(".my_cart_quantity")
        .parents('li.o_wsale_my_cart').removeClass('d-none').end()
        .toggleClass('d-none', data.cart_quantity === 0)
        .addClass('o_mycart_zoom_animation').delay(300)
        .queue(function () {
            $(this)
                .toggleClass('fa fa-warning', !data.cart_quantity)
                .attr('title', data.warning)
                .text(data.cart_quantity || '')
                .removeClass('o_mycart_zoom_animation')
                .dequeue();
        });

    $(".js_cart_lines").first().before(data['website_sale.cart_lines']).end().remove();
    $("#cart_total").replaceWith(data['website_sale.total']);
    if (data.cart_ready) {
        document.querySelector("a[name='website_sale_main_button']")?.classList.remove('disabled');
    } else {
        document.querySelector("a[name='website_sale_main_button']")?.classList.add('disabled');
    }
}

export class CustomPriceList extends Component {
    static template = "CustomPriceList";
    setup() {
        this.notification = useService("notification");
        this.state = useState({
            categories:[],
            sfilter:'all',
            active_categs:[],
            quoted: [],
            pending_quote: [],
            quote_total: 0,
            pending_total:0, 
            qpage: 1,
            ppage: 1,
            page_size: 5,
            qsearch: "",
            psearch: "",
            tab:'quoted',
            currency:'$',
            p_get_pager:{}
        });

        onWillStart(this.loadData.bind(this));
    }

    async loadData() {
        const result = await rpc("/product/quoted", {
            qpage: this.state.qpage,
            ppage: this.state.ppage,
            page_size: this.state.page_size,
            qsearch: this.state.qsearch,
            psearch: this.state.psearch,
            categs:this.state.active_categs,
            stock:this.state.sfilter
        });
        this.state.categories = result.categories; 
        this.state.quoted = result.quoted;
        this.state.pending_quote = result.pending_quote;
        this.state.total = result.total;
        this.state.currency = result.currency;
        this.state.p_get_pager = result.p_get_pager;
        this.state.q_get_pager = result.q_get_pager; 
    }

    async onSearchq(ev) {
        this.state.qsearch = ev.target.value;
        this.state.page = 1;
        await this.loadData();
    }
    async onSearchp(ev) {
        this.state.psearch = ev.target.value;
        this.state.page = 1;
        await this.loadData();
    }

    async goToPageq(page) {
        this.state.qpage = page;
        await this.loadData();
    }
    async goToPagep(page) {
        this.state.ppage = page;
        await this.loadData();
    }
    clickMin(ev){
        let parent = ev.currentTarget.parentElement;
        let inputeElem = parent.querySelector('.quantity');
        if(parseInt(inputeElem.value)-1 < 0){
            inputeElem.value = 0;
        }else{
            inputeElem.value = parseInt(inputeElem.value)-1;
        }
        
    }
    clickPlus(ev){
        let parent = ev.currentTarget.parentElement;
        let inputeElem = parent.querySelector('.quantity'); 
        inputeElem.value = parseInt(inputeElem.value) + 1; 
    }
    async clickCart(ev){ 
        let self = this; 
        let product_id = parseInt(ev.currentTarget.dataset.pid);
        let qty = ev.currentTarget.parentElement.querySelector('.quantity').value;
        await rpc('/update/shop/cart',{
            'product_id': product_id, 
            'qty': qty?parseInt(qty):0,
        }).then((data) => {
            if (data.success) {
                updateCartNavBar(data)
            }else{
                self.notification.add('Error during add to cart', {
                    title: _t("Something went wrong"),
                    type: "danger",
                });
            }
        });
    }
    async OnChangeSfilter(ev){ 
        let value = ev.target.value; 
        if(value == 'in_stock'){
            this.state.sfilter = 'in_stock';
        }else{
            this.state.sfilter = 'all';
        }
        await this.loadData();
    }
    async onChangeFilter(ev,categ){ 
        if(!ev.target.checked){
            this.state.active_categs = this.state.active_categs.filter(item => item !== categ)
        }else{ 
            this.state.active_categs.push(categ); 
        }
        await this.loadData();
    }
    get totalQuotePages() {
        return Math.ceil(this.state.quoted.length / this.state.page_size);
    }
    get totalPendingQuotePages() {
        return Math.ceil(this.state.pending_quote.length / this.state.page_size);
    }
} 
registry.category("public_components").add("custom_pricelist", CustomPriceList);
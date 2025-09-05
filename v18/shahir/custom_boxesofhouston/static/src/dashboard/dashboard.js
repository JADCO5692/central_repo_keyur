/** @odoo-module **/

import {
    Component,
    onWillStart,
    onMounted,
    useState,
    useRef, 
    onWillDestroy,
    status,
} from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks"; 
import { _t } from "@web/core/l10n/translation"; 
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { DateTimeInput } from "@web/core/datetime/datetime_input"; 
import { rpc } from "@web/core/network/rpc"; 
function get_time_frames() {
    return {
        next_week: "Next Week",
        this_week: "This Week",
        last_week: "Last Week",
        next_month: "Next Month",
        this_month: "This Month",
        last_month: "Last Month",
    };
}

class SalesDashboard extends Component {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.state = useState({
            total_sales: [],
            total_sales_amount:0,
            new_onboard_customers: [],
            quotations_sent: [],
            salesperson_summary:[],
            new_onboard_customers: [],
            total_sales_for_new_leads: [],
            all_time_frames: {},
            time_frame: 'this_month'
        });
        this.action = useService("action");
        this.notification = useService("notification");
        this.el = useRef("el");
        this.grid = useRef("grid");
        this.busService = this.env.services.bus_service;
        this.dialogService = this.env.services.dialog;

        onWillStart(async () => { 
            this.state.all_time_frames = get_time_frames(); 
            this.busService.subscribe("dashboard_notify", (params) => {
                this._onNotification(params)
            });

        });
        onMounted(async () => { 
            let defs = [];
            defs.push(this.loadDashboardData());
            await Promise.all(defs);
        }); 
        onWillDestroy(() => {
            this.busService.unsubscribe("dashboard_notify");
        });
    } 
    async _onNotification(notifications) { 
        
        if (this.state && this?.__owl__?.component && status(this.__owl__.component) != "destroyed") {
            var self = this;
            var type = notifications?.type;
            if (type && type == "record_create_notify") { 
                self.loadDashboardData();
            }
        }
    }
    loadDashboardData() { 
        try {
            var self = this;
            return rpc("/sales/data", { params: self.prepareContex() })
                .then(function (result) { 
                    self.state.salesperson_summary = result.salesperson_summary?result.salesperson_summary:[]; 
                    self.state.new_onboard_customers = result.new_onboard_customers ? result.new_onboard_customers : []; 
                    self.state.total_sales_for_new_leads = result.total_sales_for_new_leads ? result.total_sales_for_new_leads : [];
                });
        } catch (e) {
            return e;
        }
    }
    prepareContex() {
        var context = {
            time_frame: this.state.time_frame,
        };
        return Object.assign(context, {});
    }
    toggleDropdownClass(ev) {
        const parent = ev.target.parentNode;
        ev.stopPropagation();
        parent.querySelector(".dropdown-menu")?.classList.toggle("show"); 
    }
    onSelectTimeframe(ev){ 
        var $target = ev.currentTarget;
        var Tframe = $target.value || "default";
        let tframe = this.timefrrame(Tframe);
        this.state.time_frame = tframe; 
        this.loadDashboardData()
    } 
    timefrrame(tframe){  
        if (tframe == 'This Week'){
            return 'this_week';
        }
        else if (tframe == 'Last Week'){
            return 'last_week';
        } 
        else if (tframe == 'This Month'){
            return 'this_month';
        }
        else if (tframe == 'Last Month'){
            return 'last_month';
        }
        else{
            return 'this_month';
        }
    } 
    getNewCustomers(){
        let total = 0;
        if(this.state.new_onboard_customers){
            total = this.state.new_onboard_customers.reduce((sum, item) => sum + item.new_customers, 0)
        }
        return total 
    }  
    onclickCustomers(){
        let partners = this.state.new_onboard_customers.flatMap(item => item.new_customer_ids) || [];
        this.action.doAction({
            type: "ir.actions.act_window",
            name: _t("Customers"),
            res_model: "res.partner",
            views: [[false, "list"],[false, "form"],],
            domain: [["id", "in",partners]]
        });
    }
    get SmrySum(){
        let totals = this.state.salesperson_summary.reduce((acc, item) => {
            acc.new_leads += item.new_leads;
            acc.sales_amount += item.sales_amount;
            acc.quotations_sent += item.quotations_sent;
            acc.new_lead_sales += item.new_leads_sales_amount;
            return acc;
        }, { new_leads: 0, sales_amount: 0, quotations_sent: 0,new_lead_sales:0 });

        return totals
    }
}

SalesDashboard.template = "SalesDashboard";
SalesDashboard.components = {
    Dropdown,
    DropdownItem,
    DateTimeInput,
};
registry.category("actions").add("sales_dashboard_action", SalesDashboard);

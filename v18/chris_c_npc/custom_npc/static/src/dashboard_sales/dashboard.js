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
        custom: "Custom",
    };
}

class SalesDashboard extends Component {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.state = useState({ 
            all_time_frames: {},
            time_frame: 'this_month',
            new_leads_assigned: {},
            signed_contract:{},
            stage_durations:{},
            activity_complete_avg:0,
            sales_persons:[],
            start_date:'',
            end_date:'',
        });
        this.action = useService("action");
        this.notification = useService("notification");
        this.el = useRef("el");
        this.grid = useRef("grid");
        this.busService = this.env.services.bus_service;
        this.dialogService = this.env.services.dialog;

        onWillStart(async () => { 
            this.state.all_time_frames = get_time_frames();
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
            return rpc("/np/sales/data", { params: self.prepareContex() })
                .then(function (result) {  
                    self.state.new_leads_assigned = result.new_leads_assigned?result.new_leads_assigned:[]; 
                    self.state.signed_contract = result.signed_contract?result.signed_contract?.total_per_rep:[];  
                    self.state.stage_durations = result.stage_durations?result.stage_durations:[];
                    self.state.activity_complete_avg = result.activity_complete_avg?result.activity_complete_avg:0; 
                    self.state.sales_persons = result.salespersons?result.salespersons:[];  
                    console.log(self.state)
                });
        } catch (e) {
            return e;
        }
    } 
    getStageTime(avg_for){
        let avg_key = ''
        if(avg_for === "meet"){
            avg_key = 'avg_meet_days'
        }
        if(avg_for === "zoom"){
            avg_key = 'avg_zoom_days'
        }  
        let total = 0;
        let count = 0; 
        let data = this.state.stage_durations;
        for (const rep in data) {
            if (data[rep][avg_key] !== undefined) {
            total += data[rep][avg_key];
            count++;
            }
        } 
        return count > 0 ? (total / count).toFixed(1) : 0;
    }
    getNew_leads(){
        const values = Object.values(this.state.new_leads_assigned);
        if (values.length === 0) {
            return 0;
        }
        return values.reduce((sum, val) => sum + val, 0)
        // const total = values.reduce((sum, val) => sum + val, 0);
        // return Math.round(total / values.length); 
    }
    getsignedContracts(){
        const values = Object.values(this.state.signed_contract);
        if (values.length === 0) {
            return 0;
        }
        return values.reduce((sum, val) => sum + val, 0)
    } 
    // utils methods
    prepareContex() {
        var context = {
            time_frame: this.state.time_frame,
            start_date: this.state.start_date,
            end_date: this.state.end_date,
        };
        console.log(context)
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
        if(tframe != 'custom'){ 
            this.loadDashboardData()
        }
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
        else if (tframe == 'Custom'){
            return 'custom';
        }
        else{
            return 'this_month';
        }
    } 
    OnchangeDate(ev,input){
        if(input == 'start'){
            this.state.start_date = ev.currentTarget.value
        }
        if(input == 'end'){
            this.state.end_date = ev.currentTarget.value
        }
    }
    OnApplyDates(){
        this.loadDashboardData()
    }
}

SalesDashboard.template = "SalesDashboard";
SalesDashboard.components = {
    Dropdown,
    DropdownItem,
    DateTimeInput,
};
registry.category("actions").add("sales_dashboard_action", SalesDashboard);

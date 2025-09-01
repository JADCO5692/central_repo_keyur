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
            npc_data: [], 
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
            // this.busService.subscribe("dashboard_notify", (params) => {
            //     this._onNotification(params)
            // }); 

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
                    self.state.npc_data = result.npc_data?result.npc_data:[];  
                    self.render_chart()
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
    render_chart(){ 
        var ctx = document.getElementById("chart-sales-revenue").getContext("2d"); 
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.state.npc_data.labels,   
                datasets: [{
                    label: 'Revenue Amount ($)',
                    data: this.state.npc_data.values, 
                    borderColor: 'blue',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderWidth: 2,
                    tension: 0.3, 
                    fill: true,  
                    pointRadius: 5,
                    pointBackgroundColor: 'red'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return '$' + context.raw.toFixed(2);
                            }
                        }
                    },
                    datalabels: {
                        display: true,
                        align: 'top',
                        color: 'black',
                        font: {
                            weight: 'bold'
                        },
                        formatter: function(value) {
                            return "$" + value.toLocaleString();
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value;
                            }
                        }
                    }  
                }  
            },
            plugins: [ChartDataLabels]  
        });
    }
}

SalesDashboard.template = "SalesDashboard";
SalesDashboard.components = {
    Dropdown,
    DropdownItem,
    DateTimeInput,
};
registry.category("actions").add("sales_revenue_action", SalesDashboard);

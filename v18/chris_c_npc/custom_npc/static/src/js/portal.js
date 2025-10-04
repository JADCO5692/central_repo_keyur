/** @odoo-module */

import { PortalHomeCounters } from '@portal/js/portal';
import { rpc } from "@web/core/network/rpc";

PortalHomeCounters.include({
    /**
     * @override
     */
    _getCountersAlwaysDisplayed() { 
        let res = this._super(...arguments);
        let np = this.$el.data('nptype');
        if(np == 'PHYS' || np == 'none'){
            return []
        }
        return res
    },
    async _updateCounters(elem) { 
        let np = this.$el.data('nptype');
        if(np != 'PHYS' || np != 'none'){
            return this._super(...arguments);
        }else{ 
            const needed = Object.values(this.el.querySelectorAll('[data-placeholder_count]')).map(documentsCounterEl => documentsCounterEl.dataset['placeholder_count']);
            const numberRpc = Math.min(Math.ceil(needed.length / 5), 3);
            const counterByRpc = Math.ceil(needed.length / numberRpc);
            const countersAlwaysDisplayed = this._getCountersAlwaysDisplayed();
            const proms = [...Array(Math.min(numberRpc, needed.length)).keys()].map(async i => {
                const documentsCountersData = await rpc("/my/counters", {
                    counters: needed.slice(i * counterByRpc, (i + 1) * counterByRpc)
                });
                Object.keys(documentsCountersData).forEach(counterName => {
                    const documentsCounterEl = this.el.querySelector(`[data-placeholder_count='${counterName}']`);
                    documentsCounterEl.textContent = documentsCountersData[counterName];
                    // if (documentsCountersData[counterName] !== 0 || countersAlwaysDisplayed.includes(counterName)) {
                    //     documentsCounterEl.closest('.o_portal_index_card').classList.remove('d-none');
                    // }
                }
                );
                return documentsCountersData;
            }
            );
            return Promise.all(proms).then( (results) => {
                this.el.querySelector('.o_portal_doc_spinner').remove();
            }
            );
        }
    },
});

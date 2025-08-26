/** @odoo-module **/
import { FormCompiler } from "@web/views/form/form_compiler";
import { patch } from "@web/core/utils/patch";

patch(FormCompiler.prototype, {
    setup(){
        super.setup(); 
        let hash = window.location.hash?.split('#')[1]; 
        let hash_model = hash?.split('&').filter((i)=>i.split('=')[0]=='model')
         
        if(hash_model.length){
            this.form_model = hash_model[0]?.split('=')[1];
        }
    },
    
    compileForm(el, params) {
        var res = super.compileForm(el, params); 
        let self = this; 
        let result = odoo.ir_model_ids?.split(',');
        if(!result){
            result = [];
        }
        if(result.includes(self.form_model)) {
            if (odoo.web_chatter_position === "sided") {
                const classes = res.getAttribute("t-attf-class");
                const newClasses = classes.replace('{{ __comp__.uiService.size < 6 ? "flex-column" : "flex-nowrap h-100" }}', 'flex-nowrap h-100')
                res.setAttribute("t-attf-class", `${newClasses}`);
                return res;
            }

            else if (odoo.web_chatter_position === "bottom") {
                const classes = res.getAttribute("t-attf-class")
                const formView = res.getElementsByClassName('o_form_sheet_bg')[0]
                $(formView).addClass('customBottom')
                $($(formView).parent()).find('.o-mail-Form-chatter').addClass('customBottom')
                const newClasses = classes.replace('{{ __comp__.uiService.size < 6 ? "flex-column" : "flex-nowrap h-100" }}', 'flex-column')
                res.setAttribute("t-attf-class", `${newClasses}`);
                return res
            }
            return res;
        }else{
            return res;
        }
        
    },

    compile(node, params) {
        var res = super.compile(node, params);
        let result = odoo.ir_model_ids.split(',');
        if(!result){
            result = [];
        }
        var chatterContainerHookXml = res.querySelector(".o-mail-Form-chatter");
        if (!chatterContainerHookXml) {
            return res; // no chatter, keep the result as it is
        }
        let self = this;
        if(result.includes(self.form_model)) {
            if (odoo.web_chatter_position === "sided") {
                const classes = chatterContainerHookXml.getAttribute("t-attf-class")
                if(classes){
                    const newClasses = classes.replace('{{ __comp__.uiService.size >= 6 ? "o-aside" : "mt-4 mt-md-0" }}', 'o-aside')
                    res.setAttribute("t-attf-class", `${newClasses}`);
                }
                return res
            }
            else if (odoo.web_chatter_position === "bottom") {
                const classes = chatterContainerHookXml.getAttribute("t-attf-class")
                if(classes){
                    const newClasses = classes.replace('{{ __comp__.uiService.size >= 6 ? "o-aside" : "mt-4 mt-md-0" }}', 'mt-4 mt-md-0')
                    res.setAttribute("t-attf-class", `${newClasses}`);
                }
                return res
            }
        }
        return res;
        
    },
});


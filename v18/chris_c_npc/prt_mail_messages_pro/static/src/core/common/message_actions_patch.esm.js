import {_t} from "@web/core/l10n/translation";
import {messageActionsRegistry} from "@mail/core/common/message_actions";
import {toRaw, useComponent} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";
import {Deferred} from "@web/core/utils/concurrency";
import {discussComponentRegistry} from "@mail/core/common/discuss_component_registry";

messageActionsRegistry.remove("edit");
messageActionsRegistry.remove("delete");

messageActionsRegistry
    .add("msg-quote", {
        condition: (component) => component.mailMessageType,
        onClick: (component) => component.openReplyQuoteMessage(),
        icon: "fa fa-quote-left",
        title: _t("Quote"),
        sequence: 50,
    })
    .add("msg-forward", {
        condition: (component) => component.mailMessageType,
        onClick: (component) => component.openReplyForwardMessage(),
        icon: "fa fa-copy",
        title: _t("Forward"),
        sequence: 60,
    })
    .add("msg-move", {
        condition: (component) => component.mailMessageType,
        onClick: (component) => component.openMoveMessage(),
        icon: "fa fa-arrow-right",
        title: _t("Move"),
        sequence: 70,
    })
    .add("msg-delete", {
        condition: (component) => component.messageIsNotChannel,
        btnClass: "text-danger",
        icon: "fa fa-trash",
        title: _t("Delete"),
        onClick: async (component) => {
            const message = toRaw(component.message);
            const def = new Deferred();
            component.dialog.add(
                discussComponentRegistry.get("MessageConfirmDialog"),
                {
                    message,
                    prompt: _t("Are you sure you want to delete this message?"),
                    onConfirm: () => {
                        def.resolve(true);
                        message.remove();
                    },
                },
                {context: component, onClose: () => def.resolve(false)}
            );
            return def;
        },
        setup: () => {
            const component = useComponent();
            component.dialog = useService("dialog");
        },
        sequence: 90,
    })
    .add("edit", {
        condition: (component) => component.messageIsNotChannel,
        icon: "fa fa-pencil",
        title: _t("Edit"),
        onClick: (component) => component.openEditMessage(),
        sequence: 80,
    })
    .add("msg-assign", {
        condition: (component) => !component.isAuthored,
        onClick: (component) => component.openAssignAuthor(),
        icon: "fa fa-user-plus",
        title: _t("Assign"),
        sequence: 65,
    });

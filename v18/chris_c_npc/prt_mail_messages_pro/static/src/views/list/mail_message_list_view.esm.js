import {MailMessagePreviewListController} from "./mail_message_list_controller.esm";
import {MailMessagePreviewListRenderer} from "./mail_message_list_renderer.esm";
import {mailMessageListView} from "@prt_mail_messages/views/list/mail_message_list_view.esm";
import {registry} from "@web/core/registry";

export const mailMessagePreviewListView = {
    ...mailMessageListView,
    Controller: MailMessagePreviewListController,
    Renderer: MailMessagePreviewListRenderer,
    buttonTemplate: "prt_mail_messages_pro.ListView.Buttons",
};

registry
    .category("views")
    .add("prt_mail_message_preview_list", mailMessagePreviewListView);

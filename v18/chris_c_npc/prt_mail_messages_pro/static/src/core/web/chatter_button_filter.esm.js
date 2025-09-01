import {Component} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";

export class ChatterButtonFilter extends Component {
    get filterNotificationTitle() {
        return _t("Filter Notifications");
    }

    get filterNoteTitle() {
        return _t("Filter Notes");
    }

    get filterMessageTitle() {
        return _t("Filter Messages");
    }
}

ChatterButtonFilter.template = "prt_mail_messages_pro.Chatter.ButtonFilter";
ChatterButtonFilter.props = [
    "thread",
    "onClickFilterNotification",
    "onClickFilterNote",
    "onClickFilterMessage",
];

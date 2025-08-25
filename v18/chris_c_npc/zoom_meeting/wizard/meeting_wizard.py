# -*- coding: utf-8 -*-
##########################################################################
# Author : Webkul Software Pvt. Ltd. (<https://webkul.com/>;)
# Copyright(c): 2017-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>;
##########################################################################
from odoo import fields, models, api, _
from odoo.exceptions import UserError
import logging
import requests
import json
_logger = logging.getLogger(__name__)

MEETING_TYPE_OPTION = [
    ('1', 'Instant meeting'),
    ('2', 'Scheduled meeting'),
    ('3', 'Recurring meeting with no fixed time'),
    ('8', 'Recurring meeting with a fixed time'),
]


class wizardMeeting(models.TransientModel):
    _name = "wizard.zoom"
    _description = "Zoom meeting wizard"
    agenda = fields.Text("Agenda")
    alternative_hosts = fields.Text(string="Alternative Hosts")
    password = fields.Char("Password")
    host_video = fields.Boolean("Host Video")
    participant_video = fields.Boolean("Participant Video")
    joining_option = fields.Selection(
        [('joining_before_host', 'Join before Host'), ('waiting_room', "Waiting Room")], string="Joining Option")
    jbh_time = fields.Selection(
        [('0', 'Allow the participant to join the meeting at anytime'), ('5', "Allow the participant to join 5 minutes before the meeting's start time"), ('10', "Allow the participant to join 10 minutes before the meeting's start time")], string="Join before Host", help="This field indicates the time limits when a participant can join a meeting before the meeting's host.")
    mute_upon_entry = fields.Boolean("Mute Upon entry")
    watermark = fields.Boolean("Watermark")
    schedule_for_reminder = fields.Boolean(
        "Notify host and alternative host about the meeting cancellation via email", default=False)
    cancel_meeting_reminder = fields.Boolean(
        "Notify registrants about the meeting cancellation via email", default=False)
    meeting_type = fields.Selection(
        MEETING_TYPE_OPTION, string='Meeting Type', default='2',)

    allow_multiple_devices = fields.Boolean("Allow Multiple Devices")
    approval_type = fields.Selection(
        [('0', 'Automatically approve registration.'), ('1', "Manually approve registration."), ('2', "No registration required.")], string="Approval Type")
    calendar_type = fields.Selection(
        [('1', 'Zoom Outlook add-in'), ('2', " Zoom for Google Workspace add-on")], string="Calendar Type")
    enable = fields.Boolean(string="Enable continuous meeting chat")
    auto_add_invited_external_users = fields.Boolean(
        string="Automatically add invited external users")
    audio = fields.Selection([('both', 'Both telephony and VoIP.'), ('telephony', 'Telephony only.'),
                             ('voip', ' VoIP only'), ('thirdParty', 'Third party audio conference')])
    auto_recording = fields.Selection([('local', 'Record the meeting locally'), (
        'cloud', 'Record the meeting to the cloud'), ('none', 'Auto-recording disabled')])

    def call_api(self, method, data):
        """
        Call the Zoom API with the specified HTTP method and data.

        Args:
            method (str): The HTTP method to use (e.g., 'create', 'update', 'delete').
            data (dict): The data to send in the request body as a dictionary.

        Returns:
            requests.Response: The response object from the Zoom API.

        Raises:
            Exception: If there is an issue with the API request.

        Note:
            This method handles various Zoom API operations like creating, updating, or deleting meetings.
        """

        access_token = self.get_refresh_access_token()
        calendar_active_id = self._calendar_active_id()
        headers = {
            'authorization': 'Bearer ' + access_token,
            'content-type': 'application/json'
        }

        base_url = 'https://api.zoom.us/v2'
        endpoint = ''

        if method == 'create':
            response = requests.post('https://api.zoom.us/v2/users/me/meetings',
                                     headers=headers, data=json.dumps(data))
        elif method == 'update':
            response = requests.patch('https://api.zoom.us/v2/meetings/{}'.format(int(
                calendar_active_id.meeting_id)), headers=headers, data=json.dumps(data))
        else:
            response = requests.delete('https://api.zoom.us/v2/meetings/{}'.format(
                calendar_active_id.meeting_id), headers=headers, params=data)
        return response

    def meeting_create_data(self, meeting_invitees):
        calendar_active_id = self._calendar_active_id()
        meetingdetails = {
            "topic": calendar_active_id.name,
            "type": int(self.meeting_type),
            "start_time": str(calendar_active_id.start.date())+'T'+str(calendar_active_id.start.time())+'Z',
            "duration": calendar_active_id.duration*60,
            "timezone": self.env.context.get('tz'),
            "agenda": self.agenda,
            "calendar_type": int(self.calendar_type),
            "recurrence": {
                "type": 1,
                "repeat_interval": 1
            },
            "settings": {
                "host_video": self.host_video,
                "email_notification": 'true',
                "participant_video": 'true' if self.participant_video else 'false',
                "join_before_host": "true" if self.joining_option == 'joining_before_host' else "false",
                "waiting_room": "false" if self.joining_option == 'joining_before_host' else "true",
                "mute_upon_entry": 'true' if self.mute_upon_entry else 'false',
                "watermark": 'true' if self.watermark else 'false',
                "meeting_invitees": meeting_invitees,
                "audio": self.audio,
                "auto_recording": self.auto_recording,
                "allow_multiple_devices": 'true' if self.allow_multiple_devices else 'false',
                "approval_type": int(self.approval_type),
                "continuous_meeting_chat": {
                    "enable": self.enable,
                    "auto_add_invited_external_users": self.auto_add_invited_external_users
                },
            }
        }
        if self.joining_option == 'joining_before_host':
            meetingdetails['settings'].update({"jbh_time": int(self.jbh_time)})
        _logger.info(f"==meetingdetails==={meetingdetails}==")
        return meetingdetails

    def _calendar_active_id(self):
        return self.env['calendar.event'].browse(
            self._context.get('active_id'))

    def get_refresh_access_token(self):
        User = self.env.user
        Company = self.env.company

        if User.refresh_token:
            User.refresh_access_token()
            return User.access_token
        elif Company.refresh_token:
            Company.refresh_access_token()
            return Company.access_token
        else:
            raise UserError(_("First generate token in User or Company"))

    def create_zoom_meeting(self):
        access_token = self.get_refresh_access_token()
        calendar_active_id = self._calendar_active_id()
        if calendar_active_id.partner_ids:
            meeting_invitees = []
            for email in calendar_active_id.partner_ids:
                meeting_invitees.append({"email": email.email})

            meetingdetails = self.meeting_create_data(meeting_invitees)
            if self.password:
                meetingdetails.update({
                    "password": self.password,
                })

            if self.alternative_hosts:
                meetingdetails.update({
                    "alternative_hosts": self.alternative_hosts,
                })
                calendar_active_id.alternative_hosts = self.alternative_hosts
            calendar_active_id.zoom_description = meetingdetails
            try:
                r = self.call_api('create', meetingdetails)
                resp = json.loads(r.text)
                calendar_active_id.write({'meeting_id': resp.get('id', False), 'videocall_location': resp.get(
                    'join_url', False), 'start_meeting_url': resp.get('start_url', False), 'password': resp.get('password', False)})
                template_id = self.env.ref(
                    'zoom_meeting.mail_template_meeting_invitation')
                template_id.send_mail(calendar_active_id.id, force_send=True)
                return self.env['wk.wizard.message'].genrated_message("Your zoom meeting has been created", name='Message')
            except Exception as e:
                return self.env['wk.wizard.message'].genrated_message(f"{e}", name='Message')
        else:
            raise UserError(_("Please add minimum one participant"))

    def update_zoom_meeting(self):
        calendar_active_id = self._calendar_active_id()

        # Determine the 'join_before_host' and 'waiting_room' settings
        join_before_host = False
        waiting_room = False

        if self.joining_option == 'joining_before_host':
            join_before_host = True
        else:
            waiting_room = True

        # Define common settings
        settings = {
            "audio": "voip",
            "auto_recording": "cloud"
        }

        # Define the meeting details dictionary
        meeting_details = {
            "topic": calendar_active_id.name,
            "type": int(self.meeting_type),
            "start_time": str(calendar_active_id.start.date()) + 'T' + str(calendar_active_id.start.time()) + 'Z',
            "duration": calendar_active_id.duration * 60,
            "timezone": self.env.context.get('tz'),
            "recurrence": {
                "type": 1,
                "repeat_interval": 1
            },
            "settings": settings
        }

        # Update specific settings if they are provided
        if self.agenda:
            meeting_details["agenda"] = self.agenda
        if self.password:
            meeting_details["password"] = self.password

        # Update settings based on conditions
        if self.host_video:
            settings["host_video"] = 'true' if self.host_video else 'false'
        if self.participant_video:
            settings["participant_video"] = self.participant_video
        if join_before_host:
            settings["join_before_host"] = join_before_host
        else:
            settings["waiting_room"] = waiting_room
        if self.mute_upon_entry:
            settings["mute_upon_entry"] = self.mute_upon_entry
        if self.watermark:
            settings["watermark"] = self.watermark
        if self.calendar_type:
            meeting_details["calendar_type"] = self.calendar_type
        if self.audio:
            settings["audio"] = self.audio
        if self.auto_recording:
            settings["auto_recording"] = self.auto_recording
        if self.allow_multiple_devices:
            settings["allow_multiple_devices"] = self.allow_multiple_devices
        if self.approval_type:
            settings["approval_type"] = self.approval_type

        calendar_active_id.zoom_description = meeting_details

        try:
            response = self.call_api('update', meeting_details)

            if response.status_code == 204:
                return self.env['wk.wizard.message'].genrated_message("Your Zoom meeting ({}) has been updated".format(calendar_active_id.meeting_id), name='Message')
            elif response.status_code == 404:
                return self.env['wk.wizard.message'].genrated_message("User is not found or the meeting has been deleted", name='Message')
            else:
                calendar_active_id.meeting_id = False
                return self.env['wk.wizard.message'].genrated_message("There is a problem; please confirm that the meeting URL is active or the meeting is not expired", name='Message')
        except:
            return self.env['wk.wizard.message'].genrated_message("There is a problem with field data or access token; please check and try again", name='Message')

    def delete_zoom_meeting(self):
        access_token = self.get_refresh_access_token()
        calendar_active_id = self._calendar_active_id()
        try:
            params = {
                'schedule_for_reminder': self.schedule_for_reminder,
                'cancel_meeting_reminder': self.cancel_meeting_reminder
            }

            response = self.call_api('delete', params)

            if response.status_code == 204:
                calendar_active_id.meeting_id = False
                if self.schedule_for_reminder and calendar_active_id.alternative_hosts:
                    template_id = self.env.ref(
                        'zoom_meeting.mail_template_meeting_delete_alternative_hosts')
                    template_id.send_mail(
                        calendar_active_id.id, force_send=True)
                elif self.cancel_meeting_reminder:
                    template_id = self.env.ref(
                        'zoom_meeting.mail_template_meeting_delete_attendees')
                    template_id.send_mail(
                        calendar_active_id.id, force_send=True)
                return self.env['wk.wizard.message'].genrated_message("Your Zoom meeting has been deleted", name='Message')
            elif response.status_code == 404:
                return self.env['wk.wizard.message'].genrated_message("User is not found or the meeting has already been deleted", name='Message')
            else:
                calendar_active_id.meeting_id = False
                return self.env['wk.wizard.message'].genrated_message("There is a problem; please confirm that all details are correct and the user belongs to the account", name='Message')
        except:
            return self.env['wk.wizard.message'].genrated_message("There is a problem with field data or access token; please check and try again", name='Message')
            

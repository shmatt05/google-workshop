# -*- coding: utf-8 -*-
import logging
import os
from tempfile import template
from webapp2_extras.auth import InvalidAuthIdError, InvalidPasswordError
import secrets

import webapp2
from webapp2_extras import auth, sessions, jinja2
from jinja2.runtime import TemplateNotFound

from simpleauth import SimpleAuthHandler

from datetime import date, datetime, time, timedelta
import cgi
import json
import sys

import webapp2
from users_logic import user_manager

from users_logic.user_manager import DailyScheduleManager
from db import entities
from users_logic.user_manager import DailyScheduleManager
from users_logic.user_manager import UserBusinessLogic, UserView
from admin_logic.admin_manager import AdminManager, AdminViewer
from python_objects.objects import GymManager
import logging
import os
from tempfile import template
from webapp2_extras.auth import InvalidAuthIdError, InvalidPasswordError
import secrets

import webapp2
from webapp2_extras import auth, sessions, jinja2
from jinja2.runtime import TemplateNotFound

from simpleauth import SimpleAuthHandler

from datetime import date, datetime, time, timedelta
import cgi
import json
import sys

import webapp2
from users_logic import user_manager

from users_logic.user_manager import DailyScheduleManager
from db import entities
from users_logic.user_manager import DailyScheduleManager
from users_logic.user_manager import UserBusinessLogic, UserView
from admin_logic.admin_manager import AdminManager, AdminViewer
from python_objects.objects import GymManager
# -*- coding: utf-8 -*-
import logging
import os
from tempfile import template
from webapp2_extras.auth import InvalidAuthIdError, InvalidPasswordError
import secrets

import webapp2
from webapp2_extras import auth, sessions, jinja2
from jinja2.runtime import TemplateNotFound

from simpleauth import SimpleAuthHandler

from datetime import date, datetime, time
import cgi
import json
import sys

from users_logic.user_manager import DailyScheduleManager
from db import entities
from users_logic.user_manager import DailyScheduleManager
#from users_logic.user_manager import UserOperation
from admin_logic.admin_manager import AdminManager
from python_objects.objects import GymManager

def user_required(handler):
    """
      Decorator that checks if there's a user associated with the current session.
      Will also fail if there's no session present.
    """

    def check_login(self, *args, **kwargs):
        auth = self.auth
        if not auth.get_user_by_session():
            self.redirect(self.uri_for('login'), abort=True)
        else:
            return handler(self, *args, **kwargs)

    return check_login


class BaseRequestHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def jinja2(self):
        """Returns a Jinja2 renderer cached in the app registry"""
        return jinja2.get_jinja2(app=self.app)

    @webapp2.cached_property
    def session(self):
        """Returns a session using the default cookie key"""
        tmp_session = self.session_store.get_session()
        if tmp_session.get('curr_logged_in') == None:
            tmp_session['curr_logged_in'] = False
        if tmp_session.get('on_sign_up') == None:
            tmp_session['on_sign_up'] = False


        return tmp_session

    @webapp2.cached_property
    def auth(self):
        return auth.get_auth()

    @webapp2.cached_property
    def current_user(self):
        """Returns currently logged in user"""
        user_dict = self.auth.get_user_by_session()
        return self.auth.store.user_model.get_by_id(user_dict['user_id'])

    @webapp2.cached_property
    def logged_in(self):
        """Returns true if a user is currently logged in, false otherwise"""
        #return self.auth.get_user_by_session() is not None
        #print(self.session.get('curr_user_id'))

        return self.session.get('curr_logged_in') == True

    def get_user_id(self):
        """Returns user ID"""
        return self.session.get('curr_user_id')

    def render(self, template_name, template_vars={}):
        # Preset values for the template
        values = {
            'url_for': self.uri_for,
            'logged_in': self.logged_in,
            'flashes': self.session.get_flashes(),
            'session':self.session
        }

        # Add manually supplied template values
        values.update(template_vars)

        # read the template or 404.html
        try:
            self.response.write(self.jinja2.render_template(template_name, **values))
        except TemplateNotFound:
            self.abort(404)

    def head(self, *args):
        """Head is used by Twitter. If not there the tweet button shows 0"""
        pass


    #############################################################

    @webapp2.cached_property
    def user_info(self):
        """Shortcut to access a subset of the user attributes that are stored
        in the session.

        The list of attributes to store in the session is specified in
          config['webapp2_extras.auth']['user_attributes'].
        :returns
          A dictionary with most user information
        """
        return self.auth.get_user_by_session()

    @webapp2.cached_property
    def user(self):
        """Shortcut to access the current logged in user.

        Unlike user_info, it fetches information from the persistence layer and
        returns an instance of the underlying model.

        :returns
          The instance of the user model associated to the logged in user.
        """
        u = self.user_info
        return self.user_model.get_by_id(u['user_id']) if u else None

    @webapp2.cached_property
    def user_model(self):
        """Returns the implementation of the user model.

        It is consistent with config['webapp2_extras.auth']['user_model'], if set.
        """
        return self.auth.store.user_model


    def display_message(self, message):
        """Utility function to display a template with a simple message."""
        params = {
            'message': message
        }
        self.render('message.html', params)


class RootHandler(BaseRequestHandler):
    def get(self):
        """Handles default langing page"""
        self.render('home.html')


class ProfileHandler(BaseRequestHandler):
    def get(self):
        """Handles GET /profile"""
        on_sign_up = self.session.get('on_sign_up')
        #sing up
        if on_sign_up == True:
            if not user_has_session(self):
                self.display_message('The ID: %s is not valid' % id)
                return

            if self.logged_in:
                sign_up_success(self)
            else:
                self.redirect('/')
        #sign in
        else:
            check_sign_in(self)


class AuthHandler(BaseRequestHandler, SimpleAuthHandler):
    """Authentication handler for OAuth 2.0, 1.0(a) and OpenID."""

    # Enable optional OAuth 2.0 CSRF guard
    OAUTH2_CSRF_STATE = True

    USER_ATTRS = {
        'facebook': {
            'id': lambda id: ('avatar_url',
                              'http://graph.facebook.com/{0}/picture?type=large'.format(id)),
            'name': 'name',
            'link': 'link'
        },
        'google': {
            'picture': 'avatar_url',
            'name': 'name',
            'profile': 'link'
        },
        'windows_live': {
            'avatar_url': 'avatar_url',
            'name': 'name',
            'link': 'link'
        },
        'twitter': {
            'profile_image_url': 'avatar_url',
            'screen_name': 'name',
            'link': 'link'
        },
        'linkedin': {
            'picture-url': 'avatar_url',
            'first-name': 'name',
            'public-profile-url': 'link'
        },
        'linkedin2': {
            'picture-url': 'avatar_url',
            'first-name': 'name',
            'public-profile-url': 'link'
        },
        'foursquare': {
            'photo': lambda photo: ('avatar_url', photo.get('prefix') + '100x100' + photo.get('suffix')),
            'firstName': 'firstName',
            'lastName': 'lastName',
            'contact': lambda contact: ('email', contact.get('email')),
            'id': lambda id: ('link', 'http://foursquare.com/user/{0}'.format(id))
        },
        'openid': {
            'id': lambda id: ('avatar_url', '/img/missing-avatar.png'),
            'nickname': 'name',
            'email': 'link'
        }

    }

    def _on_signin(self, data, auth_info, provider):
        """Callback whenever a new or existing user is logging in.
         data is a user info dictionary.
         auth_info contains access token or oauth token and secret.
        """
        #valid_id(self)


        on_sign_up = self.session.get('on_sign_up')

        if on_sign_up == True:
            if not user_has_session(self):
                self.display_message('The ID: %s is not valid' % id)
                return

        #signed_in = self.session.get('curr_logged_in')
        #if not signed_in:


        auth_id = '%s:%s' % (provider, data['id'])
        logging.info('Looking for a user with id %s', auth_id)
        self.session['connection'] = provider
        self.session['fb_g_o'] = data['id']
        ############################################################

        user = self.auth.store.user_model.get_by_auth_id(auth_id)
        _attrs = self._to_user_model_attrs(data, self.USER_ATTRS[provider])

        if user:
            logging.info('Found existing user to log in')
            # Existing users might've changed their profile data so we update our
            # local model anyway. This might result in quite inefficient usage
            # of the Datastore, but we do this anyway for demo purposes.
            #
            # In a real app you could compare _attrs with user's properties fetched
            # from the datastore and update local user in case something's changed.
            user.populate(**_attrs)
            user.put()
            self.auth.set_session(
                self.auth.store.user_to_dict(user))

        else:
            # check whether there's a user currently logged in
            # then, create a new user if nobody's signed in,
            # otherwise add this auth_id to currently logged in user.

            if self.logged_in:
                logging.info('Updating currently logged in user')

                u = self.current_user
                u.populate(**_attrs)
                # The following will also do u.put(). Though, in a real app
                # you might want to check the result, which is
                # (boolean, info) tuple where boolean == True indicates success
                # See webapp2_extras.appengine.auth.models.User for details.
                u.add_auth_id(auth_id)

            else:
                logging.info('Creating a brand new user')
                ok, user = self.auth.store.user_model.create_user(auth_id, **_attrs)
                if ok:
                    self.auth.set_session(self.auth.store.user_to_dict(user))

        # Remember auth data during redirect, just for this demo. You wouldn't
        # normally do this.
        self.session.add_flash(data, 'data - from _on_signin(...)')
        self.session.add_flash(auth_info, 'auth_info - from _on_signin(...)')

        if on_sign_up:
            sign_up_success(self)
        else:
            check_sign_in(self)
            # Go to the profile page
            #self.redirect('/profile')

    def logout(self):
        my_logout(self)

        self.auth.unset_session()

        self.redirect('/authenticated')

    def handle_exception(self, exception, debug):
        logging.error(exception)
        self.render('error.html', {'exception': exception})

    def _callback_uri_for(self, provider):
        return self.uri_for('auth_callback', provider=provider, _full=True)

    def _get_consumer_info_for(self, provider):
        """Returns a tuple (key, secret) for auth init requests."""
        return secrets.AUTH_CONFIG[provider]

    def _to_user_model_attrs(self, data, attrs_map):
        """Get the needed information from the provider dataset."""
        user_attrs = {}
        for k, v in attrs_map.iteritems():
            attr = (v, data.get(k)) if isinstance(v, str) else v(data.get(k))
            user_attrs.setdefault(*attr)

        return user_attrs


class CheckIdHandler(BaseRequestHandler):
    def post(self):

        id = self.request.get('id')

        if not valid_id(id):
            self.display_message('The ID: %s is not valid' % id)
            return
        else:
            self.session['on_sign_up'] = True
            self.session['curr_user_id'] = id
            self.render('sign_up.html')

            #def get(self):
            #    id = self.session.get('curr_user_id')
            #    if id is None:
            #        self.display_message('The ID: %s is not valid' % id)
            #        return
            #
            #    self.render('sign_up.html')


class IdPageHandler(BaseRequestHandler):
    def get(self):
        """Handles default langing page"""
        self.render('id_page.html')


class SignInSuccessfullyHandler(BaseRequestHandler):
    def get(self):
        """Handles default langing page"""
        #template_values = {
        #        'session': {
        #            'name': course.name,
        #            'studio': course.studio,
        #            'class_key': course.id,
        #            'color': course.color,
        #            'free_slots': course.get_num_open_slots(),
        #            'start_time': course.hour[:2] + ":" + course.hour[2:],
        #            'end_time': get_end_time(long(course.milli), course.duration)
        #        }
        self.render('sign_in_successfully.html')
##########################

class LoginHandler(BaseRequestHandler):
    def get(self):
        self._serve_page()

    def post(self):

        username = self.request.get('username')
        password = self.request.get('password')
        #on_sign_up = self.session.get('on_sign_up')
        ##sing up
        #if on_sign_up == True:
        #    id = self.session.get('curr_user_id')
        #    if id is None:
        #        self.display_message('The ID: %s is not valid' % id)
        #        return

        try:
            u = self.auth.get_user_by_password(username, password, remember=True,
                                               save_session=True)

            self.session['connection'] = 'self'
            self.session['fb_g_o'] = username
            check_sign_in(self)
            #self.redirect(self.uri_for('profile'))
        except (InvalidAuthIdError, InvalidPasswordError) as e:
            logging.info('Login failed for user %s because of %s', username, type(e))
            self._serve_page(True)

    def _serve_page(self, failed=False):
        username = self.request.get('username')
        params = {
            'username': username,
            'failed': failed
        }
        self.render('login.html', params)


class VerificationHandler(BaseRequestHandler):
    def get(self, *args, **kwargs):
        if not user_has_session(self):
            self.display_message('The ID: %s is not valid' % id)
            return

        user = None
        user_id = kwargs['user_id']
        signup_token = kwargs['signup_token']
        verification_type = kwargs['type']
        #email = kwargs['email']

        # it should be something more concise like
        # self.auth.get_user_by_token(user_id, signup_token)
        # unfortunately the auth interface does not (yet) allow to manipulate
        # signup tokens concisely
        user, ts = self.user_model.get_by_auth_token(int(user_id), signup_token, 'signup')

        if not user:
            logging.info('Could not find any user with id "%s" signup token "%s"',
                         user_id, signup_token)
            self.abort(404)

        # store user data in the session
        self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)

        if verification_type == 'v':
            # remove signup token, we don't want users to come back with an old link
            self.user_model.delete_signup_token(user.get_id(), signup_token)

            if not user.verified:
                user.verified = True
                user.put()

            sign_up_success(self)
            return
        elif verification_type == 'p':
            # supply user to the page
            params = {
                'user': user,
                'token': signup_token
            }
            self.render('resetpassword.html', params)
        else:
            logging.info('verification type not supported')
            self.abort(404)


class SignupHandler(BaseRequestHandler):
    def get(self):
        #valid_id(self)
        #id = self.request.get('ID')
        #print id + "iddddddddddddd"
        #if not cheak_id():
        #     self.display_message('The ID: %s is not valid' % id)
        #     return

        if not user_has_session(self):
            self.display_message('The ID: %s is not valid' % id)
            return

        self.render('signup.html')

    def post(self):
        if not user_has_session(self):
            self.display_message('The ID: %s is not valid' % id)
            return

        user_name = self.request.get('username')
        email = self.request.get('email')
        name = self.request.get('name')
        password = self.request.get('password')
        last_name = self.request.get('lastname')

        unique_properties = ['email_address']
        user_data = self.user_model.create_user(user_name,
                                                unique_properties,
                                                email_address=email, name=name, password_raw=password,
                                                last_name=last_name, verified=False)
        if not user_data[0]: #user_data is a tuple
            self.display_message('Unable to create user for email %s because of \
        duplicate keys %s' % (user_name, user_data[1]))
            return

        user = user_data[1]
        user_id = user.get_id()

        token = self.user_model.create_signup_token(user_id)
        #store the id + connecttion way
        self.session['fb_g_o'] = email #####################################################3
        self.session['connection'] = "self"
        self.session['curr_logged_in'] = True

        verification_url = self.uri_for('verification', type='v', user_id=user_id, email=email,
                                        signup_token=token, _full=True)

        msg = 'Send an email to user in order to verify their address. \
          They will be able to do so by visiting <a href="{url}">{url}</a>'

        self.display_message(msg.format(url=verification_url))


class AuthenticatedHandler(BaseRequestHandler):
    @user_required
    def get(self):
        self.render('authenticated.html')


class ForgotPasswordHandler(BaseRequestHandler):
    def get(self):
        self._serve_page()

    def post(self):
        username = self.request.get('username')

        user = self.user_model.get_by_auth_id(username)
        if not user:
            logging.info('Could not find any user entry for username %s', username)
            self._serve_page(not_found=True)
            return

        user_id = user.get_id()
        token = self.user_model.create_signup_token(user_id)

        verification_url = self.uri_for('verification', type='p', user_id=user_id,
                                        signup_token=token, _full=True)

        msg = 'Send an email to user in order to reset their password. \
          They will be able to do so by visiting <a href="{url}">{url}</a>'

        self.display_message(msg.format(url=verification_url))

    def _serve_page(self, not_found=False):
        username = self.request.get('username')
        params = {
            'username': username,
            'not_found': not_found
        }
        self.render('forgot.html', params)


class SetPasswordHandler(BaseRequestHandler):
    @user_required
    def post(self):
        password = self.request.get('password')
        old_token = self.request.get('t')

        if not password or password != self.request.get('confirm_password'):
            self.display_message('passwords do not match')
            return

        user = self.user
        user.set_password(password)
        user.put()

        # remove signup token, we don't want users to come back with an old link
        self.user_model.delete_signup_token(user.get_id(), old_token)

        self.display_message('Password updated')

##############################


class SignUpPopUp(BaseRequestHandler):
    def post(self):
        class_key  = cgi.escape(self.request.get('class_key')) #works great!
        date_representation = cgi.escape(self.request.get('class_date'))
        date_original = date_representation
        date_representation = date_representation.split('/')
        year = date_representation[2]
        month = date_representation[1]
        day = date_representation[0]
        if not self.logged_in:
            return self.redirect('/authenticated')
        #user_viewer = UserView(self.get_user_id(), "a93cc8fa-2267-4544-a645-fbeebce41398", 2013, 12, 19)
        user_viewer = UserView(self.get_user_id(), class_key, year, month, day)
        course = user_viewer.get_course_by_id()
        code = user_viewer.get_view_code(course)
        if code == 600:
            self.render('user-popup-nocourse.html')
        else:
            template_values = {
                'course': {
                    'name':course.name,
                    'studio':course.studio,
                    'class_key':course.id,
                    'color':course.color,
                    'free_slots': course.get_num_open_slots(),
                    'start_time': course.hour[:2] + ":" + course.hour[2:],
                    'end_time': get_end_time(long(course.milli), course.duration),
                    'date': date_original
                }
            }
        #template = JINJA_ENVIRONMENT.get_template('user-popup.html')
        #self.response.write(template.render(template_values))
            self.render('user-popup.html',template_values)

class NewCoursePopup(BaseRequestHandler):
    def post(self):
        class_date  = cgi.escape(self.request.get('course_date'))
        class_hour  = cgi.escape(self.request.get('course_hour'))
        class_minutes = cgi.escape(self.request.get('course_minutes'))
        admin_viewer = AdminViewer("peer","peer")
        gym_info = admin_viewer.get_gym_info_for_popup()
        class_names = gym_info.courses_template_table
        studio_names = gym_info.studios_list
        instructor_names = gym_info.instructors_table
        template_values = {
            'class_names':class_names,
            'studio_names':studio_names,
            'instructor_names':instructor_names,
            'class_time':class_hour,
            'class_date':class_date,
            'class_minutes':class_minutes
        }
        self.render('admin-edit-course.html',template_values)

class AddClassToSched(BaseRequestHandler):
    def post(self):
        date  = cgi.escape(self.request.get('date')).split("/")
        time  = cgi.escape(self.request.get('time'))
        length  = cgi.escape(self.request.get('length'))
        participants  = cgi.escape(self.request.get('participants'))
        class_name  = cgi.escape(self.request.get('class'))
        studio  = cgi.escape(self.request.get('studio'))
        instructor  = cgi.escape(self.request.get('instructor'))
        open_date  = cgi.escape(self.request.get('open_date'))
        open_time  = cgi.escape(self.request.get('open_time'))
        all_month  = cgi.escape(self.request.get('all_month'))
        print all_month
        admin_man = AdminManager("peer", "peer")
        admin_man.create_course_for_month(class_name, time.replace(":",""),length, participants, instructor, studio,
                                          "blue", {}, {}, None, None, date[2], date[1],
                                          admin_man.get_day_by_date(int(date[2]), int(date[1]), int(date[0])))

class EditCourseTime(BaseRequestHandler):
    def post(self):
        #todo
        pass

class InitialHandler(BaseRequestHandler):
    def get(self):
        """initialize the db"""
        """create gym and put in db:"""
        admin_manager = AdminManager("peer", "peer")
        #admin_manager.create_gym("tel aviv")

        """add month schedule"""

        admin_manager.create_month_schedule(2013, 12)
        admin_manager.create_month_schedule(2013, 11)
        """create DailyScheduleManager"""
        daily_sched_manager = DailyScheduleManager(admin_manager.gym_network, admin_manager.gym_branch)
        #daily_list = daily_sched_manager.get_daily_schedule_list_from_today(3)
        #self.response.write(str(daily_list[0].day_in_week))

        """add course templates"""
        admin_manager.add_course_template("Zumba", "stupid course")
        admin_manager.add_course_template("Yoga", "ugly course")
        admin_manager.add_course_template("yoga", "ugly course")
        self.response.write(admin_manager.get_courses_templates())

        """add course template"""
        admin_manager.add_course_template("Zumba", "stupid course")
        admin_manager.add_course_template("Yoga", "ugly course")
        admin_manager.add_course_template("yoga", "ugly course") #won't succeed, because Yoga already exist
        self.response.write(admin_manager.get_courses_templates())

        """create courses"""


        admin_manager.create_course_for_month("Zumba","1400", 120, 10,
                      "Moished", "Park","blue", {}, {},"20" ,"1000", 2013, 12, 1) # December 1st 14:00 1385899200000

        admin_manager.create_course_for_month("Zumba","0900", 40, 10,
                      "Moished", "Park","green", {}, {},"1" ,"1000", 2013, 12, 2) #December 2nd 09:00 1385967600000

        admin_manager.create_course_for_month("Yoga","0700", 90, 10,
                      "Moished", "Park","blue", {}, {},"1" ,"1000", 2013, 12, 3) #December 3rd 07:00 1386046800000

        admin_manager.create_course_for_month("Yoga","1800", 90, 10,
                      "Moished", "Park","blue", {}, {},"1" ,"1000", 2013, 12, 4) #December 3rd 18:00 1386086400000

        user_credential = entities.UserCredentials()
        user_credential.id = '123'
        user_credential.gym_branch = 'peer'
        user_credential.gym_network = 'peer'
        user_credential.set_key()
        user_credential.put()
        #user 2
        user_credential = entities.UserCredentials()
        user_credential.id = '555'
        user_credential.gym_branch = 'peer'
        user_credential.gym_network = 'peer'
        user_credential.set_key()
        user_credential.put()
        #self.response.write(str(daily_list[0].courses_list[0].name))

class MainHandler(BaseRequestHandler):
    def get(self):

        admin_manager = AdminManager("peer", "peer")



        ## add

        #admin_manager.add_instructor("123456", "Roy", "Klinger")
        #admin_manager.add_instructor("1234326", "Moshe", "Tuki")
        #admin_manager.add_studio("Spinning Room")
        #admin_manager.add_studio("Yoga Room")
        #

        #
        #hour = datetime.now().hour
        #
        #admin_manager.create_course_for_month("ZumbaLatis", "Latis the Zumbot","1400", 120, 10,
        #                      "Moished", "Park","blue", [], [], 2013, 11, 3)
        #
        #
        #admin_manager.create_course_for_month("PilaYoga", "Yoga the Pila", "0930", 60, 10,
        #                      "Moished", "Park","blue", [], [], 2013, 11, 5)

###############################

        #peer = entities.Gym(name="peer", gym_network="peer", address="TLV", courses={}, instructors={}, studios=[])
        #peer.set_key()
        #peer.put()

        #creating course templates
        #zumba = objects.CourseTemplate("Zumba", "Funny course")
        #yoga = objects.CourseTemplate("Yoga", "Stupid course")

        # creating gyms

        #goactive = entities.Gym(name = "savyonim",gym_network="Go Active")

        #goactive.set_key()

        # uploading gyms to DB
        #goactive.put()


        #
        #admin = AdminManager("peer", "peer")
        #admin.add_course_template("yoga", "Zubin Meta")
        #admin.create_month_schedule(2014, 2)
        ##admin.edit_course_template("yoga","yoga11","Kaki batachton!")
        #admin.create_course_for_month("ZumbaLatis", "Latis the Zumbot", hour, 120, 10,
        #                              "Moished", "Park","blue", [], [], 2014, 2, 3)
        #day_number = admin.get_day_by_date(2013, 11, 7)
        #
        ## add user to zumbalatis
        #daily_sched_man = operations.DailyScheduleManager("peer", "peer")
        #daily_sched_man.add_user_to_course("Roy Klinger", 2014, 2, 3, hour, "ZumbaLatis")
        #daily_sched_man.add_user_to_course("Moshico Movshi", 2014, 2, 3, hour, "ZumbaLatis")
        #
        #daily = entities.MonthSchedule.get_key(2, 2014, "peer", "peer").get().schedule_table[str(3)]
        #for course in daily.courses_list:
        #    if course.name == "ZumbaLatis":
        #        self.response.write("before deletion: <br/>")
        #        for user in course.users_list:
        #            self.response.write("his name is: " + user.name + "<br/>")
        #
        #daily_sched_man.delete_user_from_course("Moshico Movshi", 2014, 2, 3, hour, "ZumbaLatis")
        #
        #daily1 = entities.MonthSchedule.get_key(2, 2014, "peer", "peer").get().schedule_table[str(3)]
        #for course in daily1.courses_list:
        #    if course.name == "ZumbaLatis":
        #        self.response.write("after deletion: <br/>")
        #        for user in course.users_list:
        #            self.response.write("his name is: " + user.name + "<br/>")
        #
        #peer_gym_after = entities.Gym.get_key("peer", "peer").get()
        #course_templates = peer_gym_after.courses
        #schedule = entities.MonthSchedule.get_key(2, 2014, "peer", "peer").get()
        #self.response.write(str(course_templates) + "<br/>")
        #self.response.write(str(schedule.schedule_table.keys()) + "<br/>")
        #self.response.write(str(schedule.schedule_table['3'].courses_list) + "<br/>")
        #self.response.write(str(day_number) + "<br/>")
        #
        ## creating real courses
        #zumba_yaron = objects.Course("Zumba", "Funny course", 1400, 60, 20, "yaron","Katom", "#FF99FF", [],[])
        #yoga_bar = objects.Course("Yoga", "Stupid course", 1700, 90, 90, "yaron", "blue", "#3399FF",[], [])
        #
        #
        ## creating schedule
        #schedule_peer = entities.MonthSchedule()
        #schedule_peer.month = 11
        #schedule_peer.year = 2013
        #schedule_peer.set_key("peer", "peer")
        #first_day = objects.DailySchedule(2013, 11, 1, 3, [zumba_yaron, yoga_bar])
        #second_day = objects.DailySchedule(2013, 11, 2, 5, [zumba_yaron, yoga_bar])
        #schedule_peer.schedule_table = {int(first_day.day_in_month): first_day, int(second_day.day_in_month): second_day}
        #
        #schedule_sav = entities.MonthSchedule()
        #schedule_sav.month = 7
        #schedule_sav.year = 2011
        #schedule_sav.set_key("Go Active", "savyonim")
        #
        #schedule_sav.put()
        #schedule_peer.put()
        #
        ##create users
        #david = objects.User(12342156, 3, 144221, "david")
        #matan = objects.User(12323126, 2, 1321, "matan")
        #omri = objects.User(123756456, 1, 1321, "omri")
        #roy = objects.User(123432356, 4, 1321, "roy")
        #
        #users = entities.Users()
        #users.set_key("peer", "peer")
        #users.users_table = users.create_users_table(david, matan, omri, roy)
        #users.put()
        #
        #users_manager = operations.DailyScheduleManager("peer", "peer")
        #start_date = datetime(day=1, month=11, year=2013)
        #end_date = datetime(day=2, month=11, year=2013)
        #
        #result = entities.MonthSchedule.get_key("11","2013","peer","peer").get()
        #if type(result.schedule_table[str(first_day.day_in_month)]) == objects.DailySchedule:
        #    self.response.write("I'm Daily Sche........!!" + "<br/>")
        #self.response.write(str(result.schedule_table[str(first_day.day_in_month)].day_in_month) + "<br/>")
        #self.response.write(str(users_manager.get_daily_schedule_list(start_date, end_date)[0].courses_list[0].studio))


class ChangeWeek(BaseRequestHandler):
    def post(self):
        users_manager = DailyScheduleManager("peer", "peer")
        gym_manager = GymManager("peer","peer")
        admin_manager = AdminManager("peer","peer")
        client_date = float(cgi.escape(self.request.get('new_date')))
        new_date = datetime.fromtimestamp(client_date/1e3)
        print new_date
        sched = admin_manager.get_weekly_daily_schedule_list_by_date(new_date)


        self.response.write(jsonpickle.encode(sched))


class AddUser(BaseRequestHandler):
    def get(self):
        david = entities.UserCredentials(id="3213908", gym_network="peer", gym_branch="peer", google_id="3241",
                                         facebook_id="4124321")
        david.set_key()
        david.put()


        user_op = UserBusinessLogic(3213908, 1111, 2013, 12, 2)


class UserHandler(BaseRequestHandler):
    def get(self):

        template_values = {

            #'mili_times': mili_times
        }

        self.render('user_grid.html',template_values)

class AdminHandler(BaseRequestHandler):
    def get(self):
        #template = JINJA_ENVIRONMENT.get_template('admin_grid.html')
        #self.response.write(template.render())
        self.render('admin_grid.html')

class CreateMonthSched(BaseRequestHandler):
    def post(self):
        full_date = cgi.escape(self.request.get('month'))
        date_arr = full_date.split('-')
        year = date_arr[0]
        month = date_arr[1]
        #self.response.write(date_arr)
        admin_man = AdminManager("peer","peer")
        admin_man.create_month_schedule(int(year), int(month))

        template_values = {
            'year': year,
            'month': month,
            'courses': admin_man.get_courses_templates(),
            'instructors': admin_man.get_instructors(),
            'studios': admin_man.get_studios()
        }
        #template = JINJA_ENVIRONMENT.get_template('create_monthly_schedule.html')
        #self.response.write(template.render(template_values))
        self.render('create_monthly_schedule.html', template_values)

class CreateMonthYear(BaseRequestHandler):

    def get(self):
        template_values = {

        }
        #template = JINJA_ENVIRONMENT.get_template('choose_month_year.html')
        #self.response.write(template.render(template_values))
        self.render('choose_month_year.html', template_values)

class AddCourse(BaseRequestHandler):

    def post(self):
        course_name = cgi.escape(self.request.get('course_name'))
        description = cgi.escape(self.request.get('description'))

        admin_man = AdminManager("peer", "peer")
        admin_man.add_course_template(course_name, description)

        template_values = {
            'year': self.request.get('year'),
            'month': self.request.get('month'),
            'courses': admin_man.get_courses_templates()
        }

        #template = JINJA_ENVIRONMENT.get_template('create_monthly_schedule.html')
        #self.response.write(template.render(template_values))
        self.render('create_monthly_schedule.html',template_values)

class CreateCourse(BaseRequestHandler):
    def post(self):
        year = cgi.escape(self.request.get('year'))
        month = cgi.escape(self.request.get('month'))
        day = cgi.escape(self.request.get('day'))
        class_name = cgi.escape(self.request.get('classes'))
        studio = cgi.escape(self.request.get('studio'))
        instructor = cgi.escape(self.request.get('instructor'))
        start_hour = cgi.escape(self.request.get('start_hour')).replace(":", "")
        duration = cgi.escape(self.request.get('duration'))
        capacity = cgi.escape(self.request.get('capacity'))

        schedule_man = DailyScheduleManager("peer", "peer")

        #print("year = "+year + " month= "+ month+ " class= " + str(class_name) + " studio= "+
        #             studio + " instructor= " + instructor + " start= " + start_hour +
        #                 " duration= " + duration + " capacity= " + capacity + " day= " + day)

        # Get description
        admin_man = AdminManager("peer", "peer")
        class_template = admin_man.get_courses_templates()[str(class_name)]
        description = class_template.description
        # Add course

        admin_man.create_course_for_month(class_name, description, start_hour, duration,capacity,instructor
           ,studio,"lavenderblush",[],[], year,month, day)
        # Get signed courses

        today = date(int(year), int(month),1)
        in_a_week = date(int(year),int(month),7)
        daily_scheduale_list = schedule_man.get_daily_schedule_list(today, in_a_week)
        singed_courses = self.get_courses_list_from_daily_schedual_list(daily_scheduale_list)
        #self.response.write("year = "+year + " month= "+ month+ " class= " + str(class_name) + " studio= "+
        #                     studio + " instructor= " + instructor + " start= " + start_hour +
        #                         " end= " + end_hour + " capacity= " + capacity +"courses list= " + str(courses))
        template_values = {
            'year': year,
            'month': month,
            'courses': admin_man.get_courses_templates(),
            'singed_courses':singed_courses
        }

        #template = JINJA_ENVIRONMENT.get_template('create_monthly_schedule.html')
        #self.response.write(template.render(template_values))
        self.render('create_monthly_schedule.html',template_values)
    def get_courses_list_from_daily_schedual_list(self, daily_schedual_list):
        result = []
        for daily in daily_schedual_list:
            result.extend(daily.courses_list)
        return result


class RegisterToClass(BaseRequestHandler):

    def post(self):
        class_key  = cgi.escape(self.request.get('class_key')) #works great!
        date_representation = cgi.escape(self.request.get('class_date'))
        date_representation = date_representation.split('/')
        year = date_representation[2]
        month = date_representation[1]
        day = date_representation[0]

        if not self.logged_in:
            return self.redirect('/authenticated')

        user_course_manager = UserBusinessLogic(self.get_user_id(), class_key, year,month, day)
        code = user_course_manager.register_to_course()
        if code == user_manager.USER_REGISTRATION_SUCCEEDED:
            self.render('user-popup-success.html')
#todo consider make users a property in gym
#todo consider make each user an entity instead of users_table


#Help functions

sys.path.insert(0, 'libs')
import jsonpickle

#JINJA_ENVIRONMENT = jinja2.Environment(
#    loader=jinja2.FileSystemLoader('templates'),
#    extensions=['jinja2.ext.autoescape'],
#    autoescape=True)

DEFAULT_GYM_NAME = "default_gym"
DEFAULT_MONTH_YEAR = "01-2001"

def to_mili(day, course):
    return time.mktime(datetime(int(day.year), int(day.month), int(day.day_in_month), int(course.hour[:2]),
                                int(course.hour[2:4])))*1000
def create_course_milli_from_daily_schedule_list(daily_sched_list):
    dict = {}
    for daily_sched in daily_sched_list:
        for course in daily_sched.courses_list:
            dict[str(course.id)] = daily_sched.javascript_course_start_datetime(course)
    return dict
def parse_course(str):
    return  str.split('_')
def get_end_time(start_time_in_milli, duration_in_minutes):
    end_date_time = datetime.fromtimestamp(start_time_in_milli/1000.0) + timedelta(0, 0, 0, 0,
                                            int(duration_in_minutes),2)
    add_zero_befor_minute = len(str(end_date_time.minute)) == 1
    add_zero_befor_hour = len(str(end_date_time.hour)) == 1

    end_time = ""

    if add_zero_befor_hour:
        end_time += "0" + str(end_date_time.hour)
    else:
        end_time += str(end_date_time.hour)

    if add_zero_befor_minute:
        end_time += ":0" + str(end_date_time.minute)
    else:
        end_time += ":" + str(end_date_time.minute)

    return end_time


"""session functions"""


def valid_id(id):
    user = entities.UserCredentials.get_user_entity(id)

    if user is None:
        #arg.display_message('The ID: %s is not valid' % id)
        return False
    else:
        return True


def sign_up_success(param_self):
    #connect user id with fb_g_o id in tables UserCredentials
    user_id = param_self.session.get('curr_user_id')
    fb_g_o = param_self.session.get('fb_g_o')
    user_from_db = entities.UserCredentials.get_user_entity(user_id)
    connection = param_self.session.get('connection')
    #connect id with fb\google\self id

    if connection == 'facebook':
        user_from_db.facebook_id = fb_g_o
        facebook_user_from_db = entities.FacebookCredentials()
        facebook_user_from_db.user_id = user_id
        facebook_user_from_db.facebook_id = fb_g_o
        facebook_user_from_db.set_key()
        facebook_user_from_db.put()
    elif connection == 'google':
        user_from_db.google_id = fb_g_o
        google_user_from_db = entities.GoogleCredentials()
        google_user_from_db.user_id = user_id
        google_user_from_db.google_id = fb_g_o
        google_user_from_db.set_key()
        google_user_from_db.put()
    elif connection == 'self':
        user_from_db.email_id = fb_g_o
        email_user_from_db = entities.EmailCredentials()
        email_user_from_db.user_id = user_id
        email_user_from_db.email_id = fb_g_o
        email_user_from_db.set_key()
        email_user_from_db.put()

    user_from_db.put()
    param_self.session['on_sign_up'] = False
    param_self.render('signup_success.html', {
        'user': param_self.current_user,
        'session': param_self.auth.get_user_by_session()})


def user_has_session(param_self):
    try:
        user_id = param_self.session['curr_user_id']
        print user_id
    except:
        return False
    return True


def check_sign_in(self_param):
    try:
        connection = self_param.session.get('connection')
        fb_g_o = self_param.session.get('fb_g_o')
        #entities.UserCredentials.get_user_entity(fb_g_o)
        #need to add self_credentials for email recognition
        #self_param.session['logged_in'] = False
        if connection == 'self':
            email_user = entities.EmailCredentials.get_key(fb_g_o).get()
            user_id = email_user.user_id
            self_param.session['curr_user_id'] = user_id
            self_param.session['curr_logged_in'] = True
            self_param.redirect('/sign_in_successfully')
        elif connection == 'facebook':
            facebook_user = entities.FacebookCredentials.get_key(fb_g_o).get()
            user_id = facebook_user.user_id
            self_param.session['curr_user_id'] = user_id
            self_param.session['curr_logged_in'] = True
            self_param.redirect('/sign_in_successfully')
        elif connection == 'google':
            google_user = entities.GoogleCredentials.get_key(fb_g_o).get()
            user_id = google_user.user_id
            self_param.session['curr_user_id'] = user_id
            self_param.session['curr_logged_in'] = True
            self_param.redirect('/sign_in_successfully')
        else:

            self_param.display_message('The ID: %s is not valid' % id)
            return
    except:

        self_param.display_message('The ID: %s is not valid' % id)
        return


def my_logout(param_self):
    param_self.session['curr_user_id'] = None
    param_self.session['fb_g_o'] = None
    param_self.session['curr_logged_in'] = False
    param_self.session['connection'] = None
    #param_self.session_store.set_secure_cookie('_simpleauth_sess', None)
    #param_self.session.cookie_name.maxAge = 0
    #param_self.response.unset_cookie('auth')
    #auth.default_config['max_age'] = 0
    #delete_cookie(key, path=’/’, domain=None)
    param_self.response.headers.add_header('Set-Cookie',
                                           'name=_simpleauth_sess; expires="Fri, 31-Dec-1954 23:59:59 GMT"')
    #param_self.redirect('https://www.facebook.com/logout.php?next=localhost:8080&access_token=USER_ACCESS_TOKEN')
    #param_self.redirect("http://www.facebook.com/logout.php?api_key={0}&;session_key={1}")
    #param_self.redirect('http://m.facebook.com/logout.php?confirm=1&next=http://localhost:8080.com;')


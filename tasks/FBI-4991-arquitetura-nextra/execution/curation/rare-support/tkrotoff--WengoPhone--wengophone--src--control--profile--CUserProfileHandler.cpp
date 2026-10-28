/*
 * WengoPhone, a voice over Internet phone
 * Copyright (C) 2004-2006  Wengo
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

#include "CUserProfileHandler.h"

#include <presentation/PFactory.h>
#include <presentation/PUserProfileHandler.h>

#include <control/profile/CUserProfile.h>

#include <model/account/wengo/WengoAccount.h>
#include <model/profile/UserProfile.h>
#include <model/profile/UserProfileHandler.h>
#include <model/WengoPhone.h>

#include <util/SafeDelete.h>
#include <thread/ThreadEvent.h>
#include <util/SafeDelete.h>

CUserProfileHandler::CUserProfileHandler(UserProfileHandler & userProfileHandler, CWengoPhone & cWengoPhone)
	: _userProfileHandler(userProfileHandler),
	_cWengoPhone(cWengoPhone) {

	_cUserProfile = NULL;

	_pUserProfileHandler = PFactory::getFactory().createPresentationUserProfileHandler(*this);

	_userProfileHandler.noCurrentUserProfileSetEvent +=
		boost::bind(&CUserProfileHandler::noCurrentUserProfileSetEventHandler, this, _1);
	_userProfileHandler.currentUserProfileWillDieEvent +=
		boost::bind(&CUserProfileHandler::currentUserProfileWillDieEventHandler, this, _1);
	_userProfileHandler.userProfileInitializedEvent +=
		boost::bind(&CUserProfileHandler::userProfileInitializedEventHandler, this, _1, _2);
	_userProfileHandler.wengoAccountNotValidEvent +=
		boost::bind(&CUserProfileHandler::wengoAccountNotValidEventHandler, this, _1, _2);
	_userProfileHandler.profileLoadedFromBackupsEvent +=
		boost::bind(&CUserProfileHandler::profileLoadedFromBackupsEventHandler, this, _1, _2);
	_userProfileHandler.profileCannotBeLoadedEvent +=
		boost::bind(&CUserProfileHandler::profileCannotBeLoadedEventHandler, this, _1, _2);
}

CUserProfileHandler::~CUserProfileHandler() {
	OWSAFE_DELETE(_pUserProfileHandler);
	OWSAFE_DELETE(_cUserProfile);
}

std::vector<std::string> CUserProfileHandler::getUserProfileNames() {
	return _userProfileHandler.getUserProfileNames();
}

void CUserProfileHandler::createAndSetUserProfile(const WengoAccount & wengoAccount) {
	typedef ThreadEvent1<void (WengoAccount), WengoAccount> MyThreadEvent;
	MyThreadEvent * event =
		new MyThreadEvent(boost::bind(&CUserProfileHandler::createAndSetUserProfileThreadSafe, this, _1), wengoAccount);

	WengoPhone::getInstance().postEvent(event);
}

void CUserProfileHandler::createAndSetUserProfileThreadSafe(WengoAccount wengoAccount) {
	_userProfileHandler.createAndSetUserProfile(wengoAccount);
}

void CUserProfileHandler::setCurrentUserProfile(const std::string & login, const WengoAccount & wengoAccount) {
	typedef ThreadEvent2<void (std::string, WengoAccount), std::string, WengoAccount> MyThreadEvent;
	MyThreadEvent * event =
		new MyThreadEvent(boost::bind(&CUserProfileHandler::setUserProfileThreadSafe, this, _1, _2),
			login, wengoAccount);

	WengoPhone::getInstance().postEvent(event);
}

void CUserProfileHandler::setUserProfileThreadSafe(std::string profileName, WengoAccount wengoAccount) {
	_userProfileHandler.setCurrentUserProfile(profileName, wengoAccount);
}

bool CUserProfileHandler::userProfileExists(const std::string & name) const {
	return _userProfileHandler.userProfileExists(name);
}

WengoAccount CUserProfileHandler::getWengoAccountOfUserProfile(const std::string & name) {
	UserProfile * userProfile = _userProfileHandler.getUserProfile(name);
	WengoAccount result(String::null, String::null, false);

	if (userProfile && userProfile->hasWengoAccount()) {
		result = *userProfile->getWengoAccount();
	}

	OWSAFE_DELETE(userProfile);

	return result;
}

void CUserProfileHandler::currentUserProfileReleased() {
	typedef ThreadEvent0<void ()> MyThreadEvent;
	MyThreadEvent * event =
		new MyThreadEvent(boost::bind(&CUserProfileHandler::currentUserProfileReleasedThreadSafe, this));

	WengoPhone::getInstance().postEvent(event);
}

void CUserProfileHandler::currentUserProfileReleasedThreadSafe() {
	OWSAFE_DELETE(_cUserProfile);

	PFactory::getFactory().reset();

	_userProfileHandler.currentUserProfileReleased();
}

void CUserProfileHandler::noCurrentUserProfileSetEventHandler(UserProfileHandler & sender) {
	_pUserProfileHandler->noCurrentUserProfileSetEventHandler();
}

void CUserProfileHandler::currentUserProfileWillDieEventHandler(UserProfileHandler & sender) {
	_pUserProfileHandler->currentUserProfileWillDieEventHandler();
}

void CUserProfileHandler::userProfileInitializedEventHandler(UserProfileHandler & sender, UserProfile & userProfile) {
	Mutex::ScopedLock scopedLock(_mutex);
	_cUserProfile = new CUserProfile(userProfile, _cWengoPhone);
	_pUserProfileHandler->userProfileInitializedEventHandler();
}

void CUserProfileHandler::wengoAccountNotValidEventHandler(UserProfileHandler & sender, WengoAccount & wengoAccount) {
	_pUserProfileHandler->wengoAccountNotValidEventHandler(wengoAccount);
}

void CUserProfileHandler::profileLoadedFromBackupsEventHandler(UserProfileStorage &sender, std::string profileName) {
	_pUserProfileHandler->profileLoadedFromBackupsEventHandler(profileName);
}

void CUserProfileHandler::profileCannotBeLoadedEventHandler(UserProfileStorage &sender, std::string profileName) {
	_pUserProfileHandler->profileCannotBeLoadedEventHandler(profileName);
}

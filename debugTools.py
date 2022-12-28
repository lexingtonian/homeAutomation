# Copyright Ari Jaaksi
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# -------------------------------------------------------------------------
# This module manages screen printings; i.e. do you want to see progress on screen
# -------------------------------------------------------------------------

ECHO = True #do you want to echo on screen
FORCE = True #a few more important notifications; yes/no?

#tools for debuggin etc
#mainly to echo stuff on terminal

def printOnTerminal(txt):
    if ECHO:
        print(txt)

def forceOnTerminal(txt):
    if FORCE:
        print(txt)
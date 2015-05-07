#
# Copyright 2015 Servionica, LLC
#
# Author: Alexander Chadin <joker946@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from oslo.config import cfg

from ceilometer import storage
from ceilometer.storage import SampleFilter
from ceilometer.alarm.evaluator.threshold import ThresholdEvaluator
from ceilometer.alarm.evaluator.combination import CombinationEvaluator
from ceilometer.openstack.common import log
from ceilometer.openstack.common.gettextutils import _

CONF = cfg.CONF
LOG = log.getLogger(__name__)


class ThresholdEvaluatorExtended(ThresholdEvaluator):

    def __init__(self, notifier):
        super(ThresholdEvaluator, self).__init__(notifier)
        self.conn = storage.get_connection_from_config(cfg.CONF, 'metering')

    def _statistics(self, alarm, query):
        for x in query:
            if x['field'] == 'resource_id':
                res = x
            elif x['field'] == 'timestamp' and x['op'] == 'ge':
                start_timestamp = x
            elif x['field'] == 'timestamp' and x['op'] == 'le':
                end_timestamp = x
        sample = SampleFilter(resource=res['value'],
                              meter=alarm.rule['meter_name'],
                              start=start_timestamp['value'],
                              start_timestamp_op=start_timestamp['op'],
                              end=end_timestamp['value'],
                              end_timestamp_op=end_timestamp['op'])
        try:
            return [i
                    for i in self.conn.get_meter_statistics(
                        sample,
                        period=alarm.rule['period']
                    )
                    ]
        except Exception:
            LOG.exception(_('alarm stats retrieval failed'))
            return []


class CombinationEvaluatorExtended(CombinationEvaluator):

    def __init__(self, notifier):
        super(CombinationEvaluator, self).__init__(notifier)
        self.conn = storage.get_connection_from_config(cfg.CONF, 'alarm')

    def _get_alarm_state(self, alarm_id):
        try:
            return self.conn.get_alarms(alarm_id=alarm_id).next().state
        except Exception:
            LOG.exception(_('alarm retrieval failed'))
            return None

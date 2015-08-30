# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import sys
import unittest
from libcloud.utils.py3 import httplib

from libcloud.common.types import InvalidCredsError
from libcloud.common.dimensiondata import DimensionDataVIPNode, DimensionDataPool
from libcloud.common.dimensiondata import DimensionDataPoolMember
from libcloud.loadbalancer.base import LoadBalancer, Member, Algorithm
from libcloud.loadbalancer.drivers.dimensiondata \
    import DimensionDataLBDriver as DimensionData
from libcloud.loadbalancer.types import State

from libcloud.test import MockHttp
from libcloud.test.file_fixtures import LoadBalancerFileFixtures

from libcloud.test.secrets import DIMENSIONDATA_PARAMS


class DimensionDataTests(unittest.TestCase):

    def setUp(self):
        DimensionData.connectionCls.conn_classes = (None, DimensionDataMockHttp)
        DimensionDataMockHttp.type = None
        self.driver = DimensionData(*DIMENSIONDATA_PARAMS)

    def test_invalid_creds(self):
        DimensionDataMockHttp.type = 'UNAUTHORIZED'
        try:
            self.driver.list_balancers()
            self.assertTrue(False)
            # Above command should have thrown an InvalidCredsException
        except InvalidCredsError:
            pass

    def test_create_balancer(self):
        self.driver.ex_set_current_network_domain('1234')
        members = []
        members.append(Member(
            id=None,
            ip='1.2.3.4',
            port=80))

        balancer = self.driver.create_balancer(
            name='test',
            port=80,
            protocol='http',
            algorithm=Algorithm.ROUND_ROBIN,
            members=members)
        self.assertEqual(balancer.name, 'test')
        self.assertEqual(balancer.id, '8334f461-0df0-42d5-97eb-f4678eb26bea')
        self.assertEqual(balancer.ip, '165.180.12.22')
        self.assertEqual(balancer.port, 80)
        self.assertEqual(balancer.extra['pool_id'], '9e6b496d-5261-4542-91aa-b50c7f569c54')
        self.assertEqual(balancer.extra['network_domain_id'], '1234')

    def test_create_balancer_no_members(self):
        self.driver.ex_set_current_network_domain('1234')
        members = None

        balancer = self.driver.create_balancer(
            name='test',
            port=80,
            protocol='http',
            algorithm=Algorithm.ROUND_ROBIN,
            members=members)
        self.assertEqual(balancer.name, 'test')
        self.assertEqual(balancer.id, '8334f461-0df0-42d5-97eb-f4678eb26bea')
        self.assertEqual(balancer.ip, '165.180.12.22')
        self.assertEqual(balancer.port, 80)
        self.assertEqual(balancer.extra['pool_id'], '9e6b496d-5261-4542-91aa-b50c7f569c54')
        self.assertEqual(balancer.extra['network_domain_id'], '1234')

    def test_create_balancer_empty_members(self):
        self.driver.ex_set_current_network_domain('1234')
        members = []

        balancer = self.driver.create_balancer(
            name='test',
            port=80,
            protocol='http',
            algorithm=Algorithm.ROUND_ROBIN,
            members=members)
        self.assertEqual(balancer.name, 'test')
        self.assertEqual(balancer.id, '8334f461-0df0-42d5-97eb-f4678eb26bea')
        self.assertEqual(balancer.ip, '165.180.12.22')
        self.assertEqual(balancer.port, 80)
        self.assertEqual(balancer.extra['pool_id'], '9e6b496d-5261-4542-91aa-b50c7f569c54')
        self.assertEqual(balancer.extra['network_domain_id'], '1234')

    def test_list_balancers(self):
        bal = self.driver.list_balancers()
        self.assertEqual(bal[0].name, 'myProduction.Virtual.Listener')
        self.assertEqual(bal[0].id, '6115469d-a8bb-445b-bb23-d23b5283f2b9')
        self.assertEqual(bal[0].port, '8899')
        self.assertEqual(bal[0].ip, '165.180.12.22')
        self.assertEqual(bal[0].state, State.RUNNING)

    def test_balancer_list_members(self):
        extra = {'pool_id': '4d360b1f-bc2c-4ab7-9884-1f03ba2768f7',
                 'network_domain_id': '1234'}
        balancer = LoadBalancer(
            id='234',
            name='test',
            state=State.RUNNING,
            ip='1.2.3.4',
            port=1234,
            driver=self.driver,
            extra=extra
        )
        members = self.driver.balancer_list_members(balancer)
        self.assertEqual(2, len(members))
        self.assertEqual(members[0].ip, '10.0.3.13')
        self.assertEqual(members[0].id, '3dd806a2-c2c8-4c0c-9a4f-5219ea9266c0')
        self.assertEqual(members[0].port, 9889)

    def test_balancer_attach_member(self):
        extra = {'pool_id': '4d360b1f-bc2c-4ab7-9884-1f03ba2768f7',
                 'network_domain_id': '1234'}
        balancer = LoadBalancer(
            id='234',
            name='test',
            state=State.RUNNING,
            ip='1.2.3.4',
            port=1234,
            driver=self.driver,
            extra=extra
        )
        member = Member(
            id=None,
            ip='112.12.2.2',
            port=80,
            balancer=balancer,
            extra=None)
        member = self.driver.balancer_attach_member(balancer, member)
        self.assertEqual(member.id, '3dd806a2-c2c8-4c0c-9a4f-5219ea9266c0')

    def test_balancer_detach_member(self):
        extra = {'pool_id': '4d360b1f-bc2c-4ab7-9884-1f03ba2768f7',
                 'network_domain_id': '1234'}
        balancer = LoadBalancer(
            id='234',
            name='test',
            state=State.RUNNING,
            ip='1.2.3.4',
            port=1234,
            driver=self.driver,
            extra=extra
        )
        member = Member(
            id='3dd806a2-c2c8-4c0c-9a4f-5219ea9266c0',
            ip='112.12.2.2',
            port=80,
            balancer=balancer,
            extra=None)
        result = self.driver.balancer_detach_member(balancer, member)
        self.assertEqual(result, True)

    def test_destroy_balancer(self):
        extra = {'pool_id': '4d360b1f-bc2c-4ab7-9884-1f03ba2768f7',
                 'network_domain_id': '1234'}
        balancer = LoadBalancer(
            id='234',
            name='test',
            state=State.RUNNING,
            ip='1.2.3.4',
            port=1234,
            driver=self.driver,
            extra=extra
        )
        response = self.driver.destroy_balancer(balancer)
        self.assertEqual(response, True)

    def test_set_get_network_domain_id(self):
        self.driver.ex_set_current_network_domain('1234')
        nwd = self.driver.ex_get_current_network_domain()
        self.assertEqual(nwd, '1234')

    def test_ex_create_pool_member(self):
        pool = DimensionDataPool(
            id='4d360b1f-bc2c-4ab7-9884-1f03ba2768f7',
            name='test',
            description='test',
            status=State.RUNNING
        )
        node = DimensionDataVIPNode(
            id='2344',
            name='test',
            status=State.RUNNING,
            ip='123.23.3.2'
        )
        member = self.driver.ex_create_pool_member(
            pool=pool,
            node=node,
            port=80
        )
        self.assertEqual(member.id, '3dd806a2-c2c8-4c0c-9a4f-5219ea9266c0')
        self.assertEqual(member.name, '10.0.3.13')
        self.assertEqual(member.ip, '123.23.3.2')

    def test_ex_create_node(self):
        node = self.driver.ex_create_node(
            network_domain_id='12345',
            name='test',
            ip='123.12.32.2',
            ex_description='',
            connection_limit=25000,
            connection_rate_limit=2000)
        self.assertEqual(node.name, 'myProductionNode.1')
        self.assertEqual(node.id, '9e6b496d-5261-4542-91aa-b50c7f569c54')

    def test_ex_create_pool(self, ):
        pool = self.driver.ex_create_pool(
            network_domain_id='1234',
            name='test',
            balancer_method='ROUND_ROBIN',
            ex_description='test',
            service_down_action='NONE',
            slow_ramp_time=30)
        self.assertEqual(pool.id, '9e6b496d-5261-4542-91aa-b50c7f569c54')
        self.assertEqual(pool.name, 'test')
        self.assertEqual(pool.status, State.RUNNING)

    def test_ex_create_virtual_listener(self):
        listener = self.driver.ex_create_virtual_listener(
            network_domain_id='12345',
            name='test',
            ex_description='test',
            port=80,
            pool=DimensionDataPool(
                id='1234',
                name='test',
                description='test',
                status=State.RUNNING
            ))
        self.assertEqual(listener.id, '8334f461-0df0-42d5-97eb-f4678eb26bea')
        self.assertEqual(listener.name, 'test')

    def test_get_balancer(self):
        bal = self.driver.get_balancer('6115469d-a8bb-445b-bb23-d23b5283f2b9')
        self.assertEqual(bal.name, 'myProduction.Virtual.Listener')
        self.assertEqual(bal.id, '6115469d-a8bb-445b-bb23-d23b5283f2b9')
        self.assertEqual(bal.port, '8899')
        self.assertEqual(bal.ip, '165.180.12.22')
        self.assertEqual(bal.state, State.RUNNING)

    def test_list_protocols(self):
        protocols = self.driver.list_protocols()
        self.assertNotEqual(0, len(protocols))

    def test_ex_get_pools(self):
        pools = self.driver.ex_get_pools()
        self.assertNotEqual(0, len(pools))
        self.assertEqual(pools[0].name, 'myDevelopmentPool.1')
        self.assertEqual(pools[0].id, '4d360b1f-bc2c-4ab7-9884-1f03ba2768f7')

    def test_ex_get_pool(self):
        pool = self.driver.ex_get_pool('4d360b1f-bc2c-4ab7-9884-1f03ba2768f7')
        self.assertEqual(pool.name, 'myDevelopmentPool.1')
        self.assertEqual(pool.id, '4d360b1f-bc2c-4ab7-9884-1f03ba2768f7')

    def test_ex_destroy_pool(self):
        response = self.driver.ex_destroy_pool(
            pool=DimensionDataPool(
                id='4d360b1f-bc2c-4ab7-9884-1f03ba2768f7',
                name='test',
                description='test',
                status=State.RUNNING))
        self.assertTrue(response)

    def test_get_pool_members(self):
        members = self.driver.ex_get_pool_members('4d360b1f-bc2c-4ab7-9884-1f03ba2768f7')
        self.assertEqual(2, len(members))
        self.assertEqual(members[0].id, '3dd806a2-c2c8-4c0c-9a4f-5219ea9266c0')
        self.assertEqual(members[0].name, '10.0.3.13')
        self.assertEqual(members[0].status, 'NORMAL')
        self.assertEqual(members[0].ip, '10.0.3.13')
        self.assertEqual(members[0].port, 9889)
        self.assertEqual(members[0].node_id, '3c207269-e75e-11e4-811f-005056806999')

    def test_get_pool_member(self):
        member = self.driver.ex_get_pool_member('3dd806a2-c2c8-4c0c-9a4f-5219ea9266c0')
        self.assertEqual(member.id, '3dd806a2-c2c8-4c0c-9a4f-5219ea9266c0')
        self.assertEqual(member.name, '10.0.3.13')
        self.assertEqual(member.status, 'NORMAL')
        self.assertEqual(member.ip, '10.0.3.13')
        self.assertEqual(member.port, 9889)

    def test_ex_destroy_pool_member(self):
        response = self.driver.ex_destroy_pool_member(
            member=DimensionDataPoolMember(
                id='',
                name='test',
                status=State.RUNNING,
                ip='1.2.3.4',
                port=80,
                node_id='3c207269-e75e-11e4-811f-005056806999'),
            destroy_node=False)
        self.assertTrue(response)

    def test_ex_destroy_pool_member_with_node(self):
        response = self.driver.ex_destroy_pool_member(
            member=DimensionDataPoolMember(
                id='',
                name='test',
                status=State.RUNNING,
                ip='1.2.3.4',
                port=80,
                node_id='34de6ed6-46a4-4dae-a753-2f8d3840c6f9'),
            destroy_node=True)
        self.assertTrue(response)


class DimensionDataMockHttp(MockHttp):

    fixtures = LoadBalancerFileFixtures('dimensiondata')

    def _oec_0_9_myaccount_UNAUTHORIZED(self, method, url, body, headers):
        return (httplib.UNAUTHORIZED, "", {}, httplib.responses[httplib.UNAUTHORIZED])

    def _oec_0_9_myaccount(self, method, url, body, headers):
        body = self.fixtures.load('oec_0_9_myaccount.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _oec_0_9_myaccount_INPROGRESS(self, method, url, body, headers):
        body = self.fixtures.load('oec_0_9_myaccount.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_virtualListener(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_virtualListener.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_virtualListener_6115469d_a8bb_445b_bb23_d23b5283f2b9(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_virtualListener_6115469d_a8bb_445b_bb23_d23b5283f2b9.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_pool(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_pool.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_pool_4d360b1f_bc2c_4ab7_9884_1f03ba2768f7(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_pool_4d360b1f_bc2c_4ab7_9884_1f03ba2768f7.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_poolMember(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_poolMember.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_poolMember_3dd806a2_c2c8_4c0c_9a4f_5219ea9266c0(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_poolMember_3dd806a2_c2c8_4c0c_9a4f_5219ea9266c0.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_createPool(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_createPool.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_createNode(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_createNode.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_addPoolMember(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_addPoolMember.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_createVirtualListener(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_createVirtualListener.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_removePoolMember(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_removePoolMember.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_deleteVirtualListener(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_deleteVirtualListener.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_deletePool(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_deletePool.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_deleteNode(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkDomainVip_deleteNode.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])


if __name__ == '__main__':
    sys.exit(unittest.main())
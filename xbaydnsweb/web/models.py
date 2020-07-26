# encoding: utf-8
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.core import validators
from xbaydns.dnsapi import nsupdate
from xbaydnsweb import conftoresults
from datetime import datetime
import traceback
import logging.config
import re,hashlib,time,copy

# TODO 联合主键失效问题

log = logging.getLogger('xbaydnsweb.web.models')


class Domain(models.Model):
    """Domain Model"""
    name = models.CharField(max_length=100,unique=True,verbose_name=_('domain_name_verbose_name'),help_text='Example:example.com.cn')
    default_ns = models.CharField(max_length=100,verbose_name=_('domain_record_ns_name'),help_text='example.com.cn.')
    record_info = models.CharField(max_length=100,verbose_name=_('domain_record_info_name'),help_text='ns1.example.com.cn.')
    a_record_info = models.CharField(max_length=100,blank=True,verbose_name=_('domain_a_record_info_name'),help_text='1.1.1.1')
    mainter = models.CharField(max_length=100,verbose_name=_('domain_maintainer'),help_text='')
    ttl = models.IntegerField(max_length=100,verbose_name=_('domain_ttl'),default=3600,help_text='3600')

    def save(self):
        from xbaydnsweb.web.utils import *
        sign = True
        if self.id != None:
            sign = False
        super(Domain,self).save()
        if sign == True:
            rt=RecordType.objects.get(record_type='NS')
            ns_record  = Record()
            ns_record.name = self.default_ns
            ns_record.domain = self
            ns_record.record_type = rt
            ns_record.record_info = self.record_info
            ns_record.ttl = self.ttl
            super(Record,ns_record).save()
            rt=RecordType.objects.get(record_type='A')
            if self.a_record_info != None:
                ans_record  = Record()
                ans_record.name = self.record_info[:self.record_info.index('.')]
                ans_record.domain = self
                ans_record.record_type = rt
                ans_record.record_info = self.a_record_info
                ans_record.ttl = self.ttl
                super(Record,ans_record).save()
        saveAllConf()
    def delete(self):
        from xbaydnsweb.web.utils import *
        super(Domain,self).delete()
        saveAllConf()
    class Admin:
        list_display = ('name',)
        list_display = ('name','mainter','ttl')
        search_fields = ('name','mainter')
        fields = (
                (_('domain_fields_domaininfo_verbose_name'), {'fields': ('name','mainter','ttl')}),
                (_('domain_fields_default_ns_verbose_name'), {'fields': ('default_ns','record_info','a_record_info')}),
        )
        #search_fields = ('name',)
    class Meta:
        ordering = ('name',)
        verbose_name = _('domain_verbose_name')
        verbose_name_plural = _('domain_verbose_name_plural')
    def __unicode__(self):
        return self.name

class IDC(models.Model):
    """IDC Model"""
    name = models.CharField(max_length=100,verbose_name=_('idc_name_verbose_name'),help_text='Example:西单机房')
    alias = models.CharField(max_length=100,verbose_name=_('idc_alias_verbose_name'),help_text='用于Agent的别名,例如:xd')


    authzcode = models.CharField(max_length=1024, blank=True,verbose_name=_('idc_authzcode_verbose_name'))
    pubkey = models.TextField(max_length=1024,blank=True, verbose_name=_('idc_pubkey_verbose_name'))
    regtime = models.DateTimeField(blank=True, null=True, verbose_name=_('idc_regtime_verbose_name'))

    class Admin:
        list_display = ('name','alias', 'authzcode', 'regtime')
        #search_fields = ('',)
        fields = (
               (_('idc_verbose_name'), {'fields': ('name','alias')}),
        )

    class Meta:
        ordering = ('name',)
        verbose_name = _('idc_verbose_name')
        verbose_name_plural = _('idc_verbose_name_plural')

    def save(self):
        from xbaydnsweb.web.utils import *
        tohash = "%s%f" % (self.alias, time.time())
        self.authzcode = hashlib.sha1(tohash).hexdigest()
        self.pubkey = ''
        super(IDC,self).save()

    def regsave(self):
        self.regtime = datetime.now()
        super(IDC,self).save()

    def __unicode__(self):
        return self.name

class Node(models.Model):
    """ Node Model """
    name = models.CharField(max_length=100, verbose_name=_('node_name_verbose_name'))
    codename = models.CharField(max_length=100, verbose_name=_('node_codename_verbose_name'))
    ip = models.CharField(max_length=100, verbose_name=_('node_ip_verbose_name'))
    type = models.CharField(max_length=32, blank=True,verbose_name=_('node_type_verbose_name'))
    authzcode = models.CharField(max_length=1024, blank=True,verbose_name=_('node_authzcode_verbose_name'))
    pubkey = models.TextField(max_length=1024,blank=True, verbose_name=_('node_pubkey_verbose_name'))
    regtime = models.DateTimeField(blank=True, null=True, verbose_name=_('node_regtime_verbose_name'))

    class Admin:
        list_display = ('name','codename', 'ip','authzcode', 'regtime')
        fields = (
               (_('node_verbose_name'), {'fields': ('name','codename','ip')}),
        )

    class Meta:
        ordering = ('name',)
        verbose_name = _('node_verbose_name')
        verbose_name_plural = _('node_verbose_name_plural')

    def save(self):
        from xbaydnsweb.web.utils import *
        self.type = 'subordinate'
        tohash = "%s%f" % (self.codename , time.time())
        self.authzcode = hashlib.sha1(tohash).hexdigest()
        self.pubkey = ''
        super(Node,self).save()
        update_allow_transfer(self.ip)
        saveAllConf(renew=False)
        
    def delete(self):
        from xbaydnsweb.web.utils import *
        super(Node,self).delete()
        saveAllConf(renew=False)
        
    def regsave(self):
        self.regtime = datetime.now()
        super(Node,self).save()

    def __unicode__(self):
        return self.name
    
class RecordType(models.Model):
    """Record types"""
    record_type = models.CharField(max_length=10,verbose_name=_('record_type'),help_text='')
    
#    class Admin:
#        list_display = ('record_type',)
        #search_fields = ('ip','record','idc')
    class Meta:
        ordering = ('record_type',)
        verbose_name = _('record_type_name')
        verbose_name_plural = _('record_type_name_plural')

    def __unicode__(self):
        return self.record_type
    
class IPArea(models.Model):
    """IP Area Management"""
    ip = models.TextField(verbose_name='',help_text='')
    view = models.CharField(max_length=100)
    acl = models.CharField(max_length=100)
    service_route = models.TextField(verbose_name='service_route',help_text='')
    route_hash = models.CharField(max_length=100,blank=True)
    
    class Admin:
        list_display = ('ip','service_route')
        #search_fields = ('ip','record','idc')
    class Meta:
        ordering = ('view','acl')
        verbose_name = _('iparea_verbose_name')
        verbose_name_plural = _('iparea_verbose_name_plural')

    def __unicode__(self):
        return self.ip

def isValiableRInfo(field_data,all_data):
    r_type = RecordType.objects.get(id=all_data['record_type'])
    if r_type.record_type == 'A':
        ipv4_re = re.compile(r'^(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}$')
        if ipv4_re.match(str(all_data['record_info'])) == None:
            raise validators.ValidationError(_('record_info_iperr'))
    elif r_type.record_type == 'CNAME':
        try:
            domain_str = all_data['record_info']
            name = domain_str[:domain_str.index('.')]
            domain = domain_str[domain_str.index('.')+1:]
            if len(Record.objects.filter(name=name,domain__name=domain)) == 0:
                raise validators.ValidationError(_('record_not_existed_a'))
        except:
            raise validators.ValidationError(_('record_syntax_err'))

def isDuplicateRecord(field_data,all_data):
    if len(Record.objects.filter(name=str(all_data['name']),domain__id=str(all_data['domain']),idc__id=str(all_data['idc']),\
                          record_type__id=str(all_data['record_type']),record_info=str(all_data['record_info']),ttl=str(all_data['ttl']))) >0:
        raise validators.ValidationError(_("duplicate_record"))
    
class Record(models.Model):
    """Record Model"""
    record_type = models.ForeignKey(RecordType,verbose_name=_('record_type_name'),validator_list=[isValiableRInfo,])
    name = models.CharField(max_length=100,verbose_name=_('record_name_verbose_name'),help_text='例如:www')
    domain = models.ForeignKey(Domain,verbose_name=_('record_domain_verbose_name'))
    idc = models.ForeignKey(IDC,verbose_name=_('record_idc_verbose_name'),blank=True,null=True)
    record_info = models.CharField(max_length=100,verbose_name=_('record_info_name'))
    ttl = models.IntegerField(verbose_name=_('record_ttl_verbose_name'),default=3600)

    def save(self):
        from xbaydnsweb.web.utils import *
        from xbaydns.conf import sysconf
        old_record = None
        if self.id != None:
            old_record = copy.deepcopy(Record.objects.get(id=self.id))
        super(Record,self).save()
        try:
            self.viewname="view_viewdefault"
            if old_record !=None:
                old_record.viewname = "view_viewdefault"
                record_delete(old_record)
            record_nsupdate(self)
            if self.record_type.record_type == 'A' and self.idc != None:
                if self.idc.alias not in getDetectedIDC():
                    for iparea in IPArea.objects.all():
                        self.viewname = iparea.view
                        if old_record !=None:
                            old_record.viewname = iparea.view
                            record_delete(old_record)
                        record_nsupdate(self)
                else:
                    if len(Record.objects.filter(idc=self.idc,record_type__record_type='A')) == 1:
                        conftoresults.main()
                        saveAllConf()
                    else:
                        if len(Record.objects.filter(name=self.name,domain=self.domain,idc=self.idc))==1:
                            conftoresults.main()
                            saveAllConf()
                        else:
                            for iparea in IPArea.objects.all():
                                if ("%s.%s"%(self.name,self.domain),self.idc.alias) in list(eval(iparea.service_route)):
                                    self.viewname = iparea.view
                                    if old_record !=None:
                                        old_record.viewname = iparea.view
                                        record_delete(old_record)
                                    record_nsupdate(self)
            else:
                for iparea in IPArea.objects.all():
                    self.viewname = iparea.view
                    if old_record !=None:
                        old_record.viewname = iparea.view
                        record_delete(old_record)
                    record_nsupdate(self)
        except:
            if self.id != None:
                super(Record,self).delete()
            print traceback.print_exc()

    def delete(self):
        from xbaydnsweb.web.utils import *
        if len(Record.objects.filter(record_type__record_type='NS',domain=self.domain))==1 and self.record_type.record_type == "NS":
            return
        self.viewname="view_viewdefault"
        record_delete(self)
        if len(Result.objects.filter(idc__alias=self.idc.alias)) != 0:
            if len(Record.objects.filter(name=self.name,domain=self.domain,idc=self.idc))==1:
                super(Record,self).delete()
                for iparea in IPArea.objects.all():
                    if ("%s.%s"%(self.name,self.domain),self.idc.alias) in list(eval(iparea.service_route)):
                        self.viewname = iparea.view
                        record_delete(self)
                conftoresults.main()
                saveAllConf()
                return
            else:
                for iparea in IPArea.objects.all():
                    if ("%s.%s"%(self.name,self.domain),self.idc.alias) in list(eval(iparea.service_route)):
                        self.viewname = iparea.view
                        record_delete(self)
        else:
            for iparea in IPArea.objects.all():
                self.viewname = iparea.view
                record_delete(self)
        super(Record,self).delete()
        
    class Admin:
        list_display = ('name','domain','record_type','record_info','ttl','idc')
        search_fields = ('name','domain','idc','record_info','record_type')
        fields = (
                (_('record_fields_domaininfo_verbose_name'), {'fields': ('record_type','name','domain','ttl')}),
                (_('record_fields_idcinfo_verbose_name'), {'fields': ('record_info','idc',)}),
        )
    class Meta:
        ordering = ('name','domain')
        verbose_name = _('record_verbose_name')
        verbose_name_plural = _('record_verbose_name_plural')
        unique_together = (("record_type","domain", "name","idc","record_info"),)
    def __unicode__(self):
        return '%s.%s in %s'%(self.name,self.domain,self.record_info)

class Result(models.Model):
    """Result Model"""
    ip = models.IPAddressField(verbose_name=_('result_ip_verbose_name'),help_text='例如:202.101.34.44')
    record = models.CharField(max_length=200,verbose_name=_('result_record_verbose_name'))
    idc = models.ForeignKey(IDC,verbose_name=_('result_idc_verbose_name'))

#    class Admin:
#        list_display = ('ip','record','idc')
        #search_fields = ('ip','record','idc')
    class Meta:
        ordering = ('record',)
        verbose_name = _('result_verbose_name')
        verbose_name_plural = _('result_verbose_name_plural')
    def __unicode__(self):
        return "%s to %s go %s"%(self.ip,self.record,self.idc)
    
class OperationInfo(models.Model):
    genview_time = models.DateTimeField(verbose_name=_('operationinfo_genview_time_name'))

class PreviewArea(models.Model):
    """IP Area Management"""
    ip = models.TextField(help_text='',verbose_name=_('iparea_ip_verbose_name'))
    view = models.CharField(max_length=100)
    acl = models.CharField(max_length=100)
    service_route = models.TextField(help_text='',verbose_name=_('iparea_service_route_verbose_name'))
    route_hash = models.CharField(max_length=100,blank=True)
    
    class Admin:
        list_display = ('ip','service_route')
    class Meta:
        verbose_name = _('previewarea_verbose_name')
        verbose_name_plural = _('previewarea_verbose_name_plural')
    def __unicode__(self):
        return self.ip
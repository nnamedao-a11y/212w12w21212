import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { API_URL, useAuth } from '../App';
import { useLang } from '../i18n';
import { toast } from 'sonner';
import { Plus, Pencil, Trash, Receipt, Eye, Target, UserPlus, ArrowsClockwise, User } from '@phosphor-icons/react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { motion } from 'framer-motion';
import QuoteHistory from '../components/crm/QuoteHistory';
import RefreshButton from '../components/ui/RefreshButton';
import PhoneInput, { detectCountry, isValidForCountry } from '../components/ui/PhoneInput';
import SharedZoneBadge from '../components/ui/SharedZoneBadge';
import ReassignDialog from '../components/ui/ReassignDialog';
import useManagersMap from '../hooks/useManagersMap';

const LEAD_STATUSES = ['new', 'contacted', 'qualified', 'proposal', 'negotiation', 'won', 'lost', 'archived'];
const LEAD_SOURCES = ['website', 'referral', 'social_media', 'cold_call', 'advertisement', 'partner', 'other'];

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const Leads = () => {
  const { t, lang } = useLang();
  const { user } = useAuth();
  const role = (user?.role || '').toLowerCase();
  const canReassign = ['admin', 'owner', 'master_admin', 'team_lead'].includes(role);
  const { managers: managersMap, invalidate: invalidateManagers } = useManagersMap();
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sourceFilter, setSourceFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingLead, setEditingLead] = useState(null);
  const [selectedLead, setSelectedLead] = useState(null);
  const [showQuoteHistory, setShowQuoteHistory] = useState(false);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [reassignTarget, setReassignTarget] = useState(null); // { ids, currentManagerId } | null
  const [formData, setFormData] = useState({
    firstName: '', lastName: '', email: '', phone: '', phoneCountry: 'BG',
    vehicleInterest: '', source: 'website', description: '', budgetEur: '',
  });
  const [formErrors, setFormErrors] = useState({});

  // Status labels with translations
  const statusLabels = {
    new: t('statusNew'),
    contacted: t('statusContacted'),
    qualified: t('statusQualified'),
    proposal: t('statusProposal'),
    negotiation: t('statusNegotiation'),
    won: t('statusWon'),
    lost: t('statusLost'),
    archived: t('statusArchived'),
  };

  // Source labels with translations
  const sourceLabels = {
    website: t('sourceWebsite'),
    referral: t('sourceReferral'),
    social_media: t('sourceSocialMedia'),
    cold_call: t('sourceColdCall'),
    advertisement: t('sourceAdvertisement'),
    partner: t('sourcePartner'),
    other: t('sourceOther'),
  };

  useEffect(() => {
    fetchLeads();
  }, [search, statusFilter, sourceFilter]);

  const fetchLeads = async () => {
    try {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (statusFilter) params.append('status', statusFilter);
      if (sourceFilter) params.append('source', sourceFilter);
      
      const res = await axios.get(`${API_URL}/api/leads?${params}`);
      setLeads(res.data.data || []);
    } catch (err) {
      toast.error(t('error'));
    } finally {
      setLoading(false);
    }
  };

  const validate = () => {
    const errors = {};
    if (!(formData.firstName || '').trim()) errors.firstName = t('field_required');
    if (!(formData.lastName || '').trim()) errors.lastName = t('field_required');
    if (!(formData.email || '').trim()) {
      errors.email = t('field_required');
    } else if (!EMAIL_RE.test(formData.email.trim())) {
      errors.email = t('field_invalid_email');
    }
    // Phone is optional, but if entered must validate against the country.
    if (formData.phone && !isValidForCountry(formData.phone, formData.phoneCountry)) {
      errors.phone = t('field_invalid_phone');
    }
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) {
      toast.error(t('field_form_invalid'));
      return;
    }
    try {
      const payload = {
        firstName: formData.firstName.trim(),
        lastName:  formData.lastName.trim(),
        email:     formData.email.trim(),
        phone:     formData.phone || null,
        phoneCountry: formData.phoneCountry || null,
        vehicleInterest: formData.vehicleInterest || null,
        source:    formData.source,
        description: formData.description || null,
        budgetEur: Number(formData.budgetEur) || 0,
      };
      if (editingLead) {
        await axios.put(`${API_URL}/api/leads/${editingLead.id}`, payload);
        toast.success(t('success'));
      } else {
        await axios.post(`${API_URL}/api/leads`, payload);
        toast.success(t('success'));
      }
      setShowModal(false);
      resetForm();
      fetchLeads();
    } catch (err) {
      toast.error(err.response?.data?.detail || err.response?.data?.message || t('error'));
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm(lang === 'uk' ? t('adm3_9a8de0b327') : 'Delete this lead?')) return;
    try {
      await axios.delete(`${API_URL}/api/leads/${id}`);
      toast.success(t('success'));
      fetchLeads();
    } catch (err) {
      toast.error(t('error'));
    }
  };

  const handleStatusChange = async (id, newStatus) => {
    try {
      await axios.put(`${API_URL}/api/leads/${id}`, { status: newStatus });
      toast.success(t('success'));
      fetchLeads();
    } catch (err) {
      toast.error(err.response?.data?.message || t('error'));
    }
  };

  const handleConvert = async (lead) => {
    if (lead.customerId) {
      toast.info(t('lead_already_customer') || 'Lead is already linked to a customer');
      return;
    }
    const msg = t('lead_convert_confirm') || 'Convert this lead into a customer?';
    if (!window.confirm(msg)) return;
    try {
      const res = await axios.post(`${API_URL}/api/leads/${lead.id}/convert`);
      const customerId = res?.data?.customer?.id;
      toast.success(t('lead_convert_done') || 'Lead converted to customer');
      fetchLeads();
      if (customerId) {
        // Best-effort deep-link to the new customer card
        setTimeout(() => { window.location.href = `/admin/customers?focus=${customerId}`; }, 600);
      }
    } catch (err) {
      const msg = err.response?.data?.detail || err.response?.data?.message || t('lead_convert_failed') || 'Failed to convert lead';
      toast.error(msg);
    }
  };

  const openEditModal = (lead) => {
    setEditingLead(lead);
    // Try to detect country from saved phone; fall back to saved phoneCountry or BG.
    const detected = detectCountry(lead.phone);
    setFormData({
      firstName: lead.firstName || '',
      lastName:  lead.lastName || '',
      email:     lead.email || '',
      phone:     lead.phone || '',
      phoneCountry: lead.phoneCountry || (detected && detected.code) || 'BG',
      vehicleInterest: lead.vehicleInterest || lead.company || '',
      source:    lead.source || 'website',
      description: lead.description || lead.notes || '',
      budgetEur: lead.budgetEur || lead.budgetUsd || lead.value || lead.price || '',
    });
    setFormErrors({});
    setShowModal(true);
  };

  const resetForm = () => {
    setEditingLead(null);
    setFormData({
      firstName: '', lastName: '', email: '', phone: '', phoneCountry: 'BG',
      vehicleInterest: '', source: 'website', description: '', budgetEur: '',
    });
    setFormErrors({});
  };

  return (
    <motion.div 
      data-testid="leads-page"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex flex-row items-start justify-between gap-3 sm:gap-4 mb-6 lg:mb-8">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <div className="w-10 h-10 rounded-xl bg-[#18181B] text-white flex items-center justify-center shrink-0">
            <Target size={18} weight="duotone" />
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[#18181B] leading-tight break-words" style={{ fontFamily: 'Mazzard, Mazzard H, Mazzard M, system-ui, sans-serif' }}>
              {t('leadsTitle')}
            </h1>
            <p className="text-xs sm:text-sm text-[#71717A] mt-1 break-words">{t('leadManagement')}</p>
            <div className="mt-2">
              <SharedZoneBadge />
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <RefreshButton onClick={fetchLeads} loading={loading} ariaLabel={t('adm_refresh_3') || 'Refresh'} testId="leads-refresh-btn" />
          <button
            onClick={() => { resetForm(); setShowModal(true); }}
            className="btn-primary shrink-0 whitespace-nowrap"
            data-testid="create-lead-btn"
          >
            <Plus size={18} weight="bold" />
            <span className="hidden sm:inline">{t('newLead')}</span>
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4 sm:p-5 mb-4 sm:mb-5">
        <div className="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-3 sm:gap-4">
          <div className="flex-1 min-w-0 sm:min-w-[200px] sm:max-w-md">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={t('searchByNameEmailPhone')}
              className="input w-full"
              data-testid="leads-search-input"
            />
          </div>
          <div className="flex gap-3">
            <Select value={statusFilter || "all"} onValueChange={(v) => setStatusFilter(v === "all" ? "" : v)}>
              <SelectTrigger className="w-full sm:w-[160px] h-[46px] bg-white border border-[#E4E4E7] rounded-xl" data-testid="leads-status-filter">
                <SelectValue placeholder={t('allStatuses')} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t('allStatuses')}</SelectItem>
                {LEAD_STATUSES.map(s => (
                  <SelectItem key={s} value={s}>{statusLabels[s]}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={sourceFilter || "all"} onValueChange={(v) => setSourceFilter(v === "all" ? "" : v)}>
              <SelectTrigger className="w-full sm:w-[160px] h-[46px] bg-white border border-[#E4E4E7] rounded-xl" data-testid="leads-source-filter">
                <SelectValue placeholder={t('allSources')} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t('allSources')}</SelectItem>
                {LEAD_SOURCES.map(s => (
                  <SelectItem key={s} value={s}>{sourceLabels[s]}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Table - desktop / tablet */}
      <div className="card overflow-hidden">
        {/* Bulk action bar */}
        {canReassign && selectedIds.size > 0 && (
          <div className="bg-[#EEF2FF] border-b border-[#C7D2FE] px-4 py-2.5 flex items-center justify-between gap-3" data-testid="leads-bulk-bar">
            <div className="text-sm text-[#3730A3] font-medium">
              {selectedIds.size} {selectedIds.size === 1 ? 'lead' : 'leads'} selected
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setReassignTarget({ ids: Array.from(selectedIds), currentManagerId: null })}
                className="px-3 py-1.5 bg-[#4F46E5] hover:bg-[#4338CA] text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 transition-colors"
                data-testid="leads-bulk-reassign"
              >
                <ArrowsClockwise size={14} weight="bold" /> Reassign selected
              </button>
              <button
                onClick={() => setSelectedIds(new Set())}
                className="px-3 py-1.5 text-[#52525B] hover:bg-white text-xs font-medium rounded-lg transition-colors"
              >
                Clear
              </button>
            </div>
          </div>
        )}
        <div className="hidden md:block overflow-x-auto -mx-0 sm:mx-0">
          <table className="table-premium min-w-[800px] w-full" data-testid="leads-table">
          <thead>
            <tr>
              {canReassign && (
                <th className="w-10 text-center">
                  <input
                    type="checkbox"
                    aria-label="Select all"
                    checked={leads.length > 0 && selectedIds.size === leads.length}
                    onChange={(e) => {
                      if (e.target.checked) setSelectedIds(new Set(leads.map(l => l.id)));
                      else setSelectedIds(new Set());
                    }}
                    className="rounded border-[#A1A1AA] text-[#4F46E5] focus:ring-[#4F46E5]"
                    data-testid="leads-select-all"
                  />
                </th>
              )}
              <th>{t('name')}</th>
              <th>{t('vin')}</th>
              <th>{t('email')}</th>
              <th>{t('source')}</th>
              <th>{t('status')}</th>
              <th>Manager</th>
              <th>{t('clientPrice')}</th>
              <th>{t('internalPrice')}</th>
              <th className="text-right">{t('actions')}</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={canReassign ? 10 : 9} className="text-center py-12 text-[#71717A]">
                <div className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-2 border-[#18181B] border-t-transparent rounded-full animate-spin"></div>
                  {t('loading')}
                </div>
              </td></tr>
            ) : leads.length === 0 ? (
              <tr><td colSpan={canReassign ? 10 : 9} className="text-center py-12 text-[#71717A]">{t('noLeads')}</td></tr>
            ) : leads.map(lead => {
              const mgr = lead.managerId ? managersMap[lead.managerId] : null;
              const isSelected = selectedIds.has(lead.id);
              return (
              <tr key={lead.id} data-testid={`lead-row-${lead.id}`} className={isSelected ? 'bg-[#F5F3FF]' : ''}>
                {canReassign && (
                  <td className="w-10 text-center">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={(e) => {
                        const next = new Set(selectedIds);
                        if (e.target.checked) next.add(lead.id);
                        else next.delete(lead.id);
                        setSelectedIds(next);
                      }}
                      className="rounded border-[#A1A1AA] text-[#4F46E5] focus:ring-[#4F46E5]"
                      data-testid={`lead-select-${lead.id}`}
                    />
                  </td>
                )}
                <td className="font-medium text-[#18181B]">{lead.firstName} {lead.lastName}</td>
                <td className="font-mono text-xs text-[#71717A]">{lead.vin || '—'}</td>
                <td>{lead.email || '—'}</td>
                <td><span className="text-xs text-[#71717A]">{sourceLabels[lead.source]}</span></td>
                <td>
                  <Select value={lead.status} onValueChange={(v) => handleStatusChange(lead.id, v)}>
                    <SelectTrigger className="w-[130px] h-8 bg-transparent border-0 p-0" data-testid={`lead-status-${lead.id}`}>
                      <span className={`badge status-${lead.status}`}>{statusLabels[lead.status]}</span>
                    </SelectTrigger>
                    <SelectContent>
                      {LEAD_STATUSES.map(s => (
                        <SelectItem key={s} value={s}>{statusLabels[s]}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </td>
                <td>
                  {mgr ? (
                    <div className="flex items-center gap-1.5 text-xs">
                      <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#4F46E5] to-[#7C3AED] text-white flex items-center justify-center font-semibold text-[10px]">
                        {(mgr.name || mgr.email || '?').slice(0,1).toUpperCase()}
                      </div>
                      <span className="text-[#18181B] truncate max-w-[110px]" title={mgr.email}>{mgr.name || mgr.email}</span>
                    </div>
                  ) : (
                    <span className="text-xs text-[#A1A1AA] italic">unassigned</span>
                  )}
                </td>
                <td className="text-[#059669] font-medium">${lead.price?.toLocaleString() || 0}</td>
                <td className="text-[#7C3AED] font-semibold">
                  ${lead.metadata?.internalTotal?.toLocaleString() || lead.price?.toLocaleString() || 0}
                  {lead.metadata?.hiddenFee > 0 && (
                    <span className="text-xs text-[#71717A] ml-1">(+${lead.metadata?.hiddenFee})</span>
                  )}
                </td>
                <td>
                  <div className="flex items-center justify-end gap-1">
                    {canReassign && (
                      <button
                        onClick={() => setReassignTarget({ ids: [lead.id], currentManagerId: lead.managerId })}
                        className="p-2.5 hover:bg-[#EEF2FF] rounded-lg transition-colors"
                        data-testid={`reassign-lead-${lead.id}`}
                        title="Reassign to another manager"
                      >
                        <ArrowsClockwise size={16} className="text-[#4F46E5]" />
                      </button>
                    )}
                    <button 
                      onClick={() => { setSelectedLead(lead); setShowQuoteHistory(true); }}
                      className="p-2.5 hover:bg-[#DBEAFE] rounded-lg transition-colors" 
                      data-testid={`quotes-lead-${lead.id}`}
                      title={t('adm_settlement_history')}
                    >
                      <Receipt size={16} className="text-[#2563EB]" />
                    </button>
                    <button
                      onClick={() => handleConvert(lead)}
                      disabled={!!lead.customerId}
                      className={`p-2.5 rounded-lg transition-colors ${lead.customerId ? 'opacity-30 cursor-not-allowed' : 'hover:bg-[#DCFCE7]'}`}
                      data-testid={`convert-lead-${lead.id}`}
                      title={lead.customerId ? (t('lead_already_customer') || 'Already linked to customer') : (t('lead_convert_btn') || 'Convert to Customer')}
                    >
                      <UserPlus size={16} className={lead.customerId ? 'text-[#71717A]' : 'text-[#16A34A]'} />
                    </button>
                    <button 
                      onClick={() => openEditModal(lead)} 
                      className="p-2.5 hover:bg-[#F4F4F5] rounded-lg transition-colors" 
                      data-testid={`edit-lead-${lead.id}`}
                    >
                      <Pencil size={16} className="text-[#71717A]" />
                    </button>
                    <button 
                      onClick={() => handleDelete(lead.id)} 
                      className="p-2.5 hover:bg-[#FEE2E2] rounded-lg transition-colors" 
                      data-testid={`delete-lead-${lead.id}`}
                    >
                      <Trash size={16} className="text-[#DC2626]" />
                    </button>
                  </div>
                </td>
              </tr>
            )})}
          </tbody>
        </table>
        </div>

        {/* Mobile — stacked card view (parity with Customers.js) */}
        <div className="md:hidden divide-y divide-[#F4F4F5]" data-testid="leads-mobile-list">
          {loading ? (
            <div className="text-center py-12 text-[#71717A]">
              <div className="flex items-center justify-center gap-2">
                <div className="w-5 h-5 border-2 border-[#18181B] border-t-transparent rounded-full animate-spin"></div>
                {t('loading')}
              </div>
            </div>
          ) : leads.length === 0 ? (
            <div className="text-center py-12 text-[#71717A]">{t('noLeads')}</div>
          ) : leads.map(lead => (
            <div
              key={lead.id}
              className="p-4 hover:bg-[#FAFAFA] transition-colors"
              data-testid={`lead-card-${lead.id}`}
            >
              <div className="flex items-start justify-between gap-3 mb-2">
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-[#18181B] text-base truncate">
                    {lead.firstName} {lead.lastName}
                  </div>
                  {lead.email && (
                    <div className="text-xs text-[#71717A] truncate mt-0.5">{lead.email}</div>
                  )}
                </div>
                <div className="flex items-center gap-1 flex-shrink-0">
                  <button
                    onClick={() => { setSelectedLead(lead); setShowQuoteHistory(true); }}
                    className="p-2 hover:bg-[#DBEAFE] rounded-lg"
                    data-testid={`quotes-lead-mob-${lead.id}`}
                    title={t('adm_settlement_history')}
                  >
                    <Receipt size={16} className="text-[#2563EB]" />
                  </button>
                  <button
                    onClick={() => handleConvert(lead)}
                    disabled={!!lead.customerId}
                    className={`p-2 rounded-lg ${lead.customerId ? 'opacity-30 cursor-not-allowed' : 'hover:bg-[#DCFCE7]'}`}
                    data-testid={`convert-lead-mob-${lead.id}`}
                    title={lead.customerId ? (t('lead_already_customer') || 'Already linked to customer') : (t('lead_convert_btn') || 'Convert to Customer')}
                  >
                    <UserPlus size={16} className={lead.customerId ? 'text-[#71717A]' : 'text-[#16A34A]'} />
                  </button>
                  <button onClick={() => openEditModal(lead)} className="p-2 hover:bg-[#F4F4F5] rounded-lg" data-testid={`edit-lead-mob-${lead.id}`}>
                    <Pencil size={16} className="text-[#71717A]" />
                  </button>
                  <button onClick={() => handleDelete(lead.id)} className="p-2 hover:bg-[#FEE2E2] rounded-lg" data-testid={`delete-lead-mob-${lead.id}`}>
                    <Trash size={16} className="text-[#DC2626]" />
                  </button>
                </div>
              </div>

              <div className="mb-2">
                <Select value={lead.status} onValueChange={(v) => handleStatusChange(lead.id, v)}>
                  <SelectTrigger className="h-8 w-auto bg-transparent border-0 p-0" data-testid={`lead-status-mob-${lead.id}`}>
                    <span className={`badge status-${lead.status}`}>{statusLabels[lead.status]}</span>
                  </SelectTrigger>
                  <SelectContent>
                    {LEAD_STATUSES.map(s => (
                      <SelectItem key={s} value={s}>{statusLabels[s]}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-sm">
                {lead.phone && (
                  <div>
                    <span className="text-[10px] uppercase tracking-wider text-[#A1A1AA]">{t('phone')}</span>
                    <div className="text-[#18181B] truncate">{lead.phone}</div>
                  </div>
                )}
                {lead.source && (
                  <div>
                    <span className="text-[10px] uppercase tracking-wider text-[#A1A1AA]">{t('source')}</span>
                    <div className="text-[#71717A] truncate">{sourceLabels[lead.source]}</div>
                  </div>
                )}
                {lead.vehicleInterest && (
                  <div className="col-span-2">
                    <span className="text-[10px] uppercase tracking-wider text-[#A1A1AA]">{t('lead_vehicle_interest') || 'Vehicle of interest'}</span>
                    <div className="text-[#18181B] truncate">{lead.vehicleInterest}</div>
                  </div>
                )}
                {(lead.price || lead.budgetEur || lead.budgetUsd) ? (
                  <div className="col-span-2 flex items-center justify-between pt-1 border-t border-[#F4F4F5]">
                    <span className="text-[10px] uppercase tracking-wider text-[#A1A1AA]">{t('clientPrice')}</span>
                    <span className="text-[#059669] font-semibold">
                      ${(lead.price || lead.budgetEur || lead.budgetUsd || 0).toLocaleString()}
                    </span>
                  </div>
                ) : null}
                <div className="col-span-2 flex items-center justify-between pt-1 border-t border-[#F4F4F5]">
                  <span className="text-[10px] uppercase tracking-wider text-[#A1A1AA]">Manager</span>
                  {lead.managerId && managersMap[lead.managerId] ? (
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-[#18181B] truncate max-w-[140px]">{managersMap[lead.managerId].name || managersMap[lead.managerId].email}</span>
                      {canReassign && (
                        <button
                          onClick={() => setReassignTarget({ ids: [lead.id], currentManagerId: lead.managerId })}
                          className="p-1.5 hover:bg-[#EEF2FF] rounded-lg transition-colors"
                          data-testid={`reassign-lead-mob-${lead.id}`}
                          title="Reassign"
                        >
                          <ArrowsClockwise size={14} className="text-[#4F46E5]" />
                        </button>
                      )}
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-[#A1A1AA] italic">unassigned</span>
                      {canReassign && (
                        <button
                          onClick={() => setReassignTarget({ ids: [lead.id], currentManagerId: null })}
                          className="px-2 py-1 bg-[#4F46E5] text-white text-[10px] font-semibold rounded-md"
                          data-testid={`reassign-lead-mob-${lead.id}`}
                        >
                          Assign
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Modal */}
      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="max-w-[calc(100%-2rem)] sm:max-w-md bg-white rounded-2xl border border-[#E4E4E7] max-h-[90vh] overflow-y-auto" data-testid="lead-modal">
          <DialogHeader>
            <DialogTitle className="text-lg sm:text-xl font-bold text-[#18181B]" style={{ fontFamily: 'Mazzard, Mazzard H, Mazzard M, system-ui, sans-serif' }}>
              {editingLead ? t('editLead') : t('newLead')}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-5 mt-4">
            {/* Helper banner — explains how leads relate to customers/deals */}
            <div className="rounded-xl bg-[#F0F9FF] border border-[#0EA5E9]/30 px-3 py-2 text-[12px] text-[#075985] leading-relaxed">
              {t('lead_helper_banner')}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#71717A] mb-2">{t('firstName')} <span className="text-[#DC2626]">*</span></label>
                <input
                  type="text"
                  value={formData.firstName}
                  onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
                  required
                  className={`input w-full ${formErrors.firstName ? 'border-[#DC2626] focus:ring-[#DC2626]/30' : ''}`}
                  data-testid="lead-firstname-input"
                />
                {formErrors.firstName ? <p className="mt-1.5 text-[11px] text-[#DC2626]">{formErrors.firstName}</p> : null}
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#71717A] mb-2">{t('lastName')} <span className="text-[#DC2626]">*</span></label>
                <input
                  type="text"
                  value={formData.lastName}
                  onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
                  required
                  className={`input w-full ${formErrors.lastName ? 'border-[#DC2626] focus:ring-[#DC2626]/30' : ''}`}
                  data-testid="lead-lastname-input"
                />
                {formErrors.lastName ? <p className="mt-1.5 text-[11px] text-[#DC2626]">{formErrors.lastName}</p> : null}
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-[#71717A] mb-2">{t('email')} <span className="text-[#DC2626]">*</span></label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
                className={`input w-full ${formErrors.email ? 'border-[#DC2626] focus:ring-[#DC2626]/30' : ''}`}
                data-testid="lead-email-input"
                placeholder="name@example.com"
              />
              {formErrors.email ? <p className="mt-1.5 text-[11px] text-[#DC2626]">{formErrors.email}</p> : null}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#71717A] mb-2">{t('phone')}</label>
                <PhoneInput
                  value={formData.phone}
                  country={formData.phoneCountry}
                  onChange={({ phone, country }) => setFormData({ ...formData, phone, phoneCountry: country })}
                  error={formErrors.phone}
                  testId="lead-phone"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#71717A] mb-2">{t('lead_vehicle_interest')}</label>
                <input
                  type="text"
                  value={formData.vehicleInterest}
                  onChange={(e) => setFormData({ ...formData, vehicleInterest: e.target.value })}
                  className="input w-full"
                  placeholder={t('lead_vehicle_interest_ph')}
                  data-testid="lead-vehicle-interest-input"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#71717A] mb-2">{t('source')}</label>
                <Select value={formData.source} onValueChange={(v) => setFormData({ ...formData, source: v })}>
                  <SelectTrigger className="input w-full" data-testid="lead-source-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {LEAD_SOURCES.map((s) => (
                      <SelectItem key={s} value={s}>{sourceLabels[s]}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#71717A] mb-2">{t('lead_budget_eur')}</label>
                <input
                  type="number"
                  min="0"
                  step="500"
                  value={formData.budgetEur}
                  onChange={(e) => setFormData({ ...formData, budgetEur: e.target.value === '' ? '' : (parseInt(e.target.value, 10) || 0) })}
                  className="input w-full"
                  placeholder={t('lead_budget_ph') || '25000'}
                  data-testid="lead-budget-input"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-[#71717A] mb-2">{t('description')}</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                className="input w-full resize-none"
                placeholder={t('lead_description_ph')}
                data-testid="lead-description-input"
              />
            </div>

            <div className="flex gap-3 pt-2">
              <button type="button" onClick={() => setShowModal(false)} className="btn-secondary flex-1" data-testid="lead-cancel-btn">{t('cancel')}</button>
              <button type="submit" className="btn-primary flex-1" data-testid="lead-submit-btn">{editingLead ? t('save') : t('create')}</button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Quote History Modal */}
      <Dialog open={showQuoteHistory} onOpenChange={setShowQuoteHistory}>
        <DialogContent className="max-w-3xl bg-white rounded-2xl border border-[#E4E4E7]" data-testid="quote-history-modal">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold text-[#18181B]" style={{ fontFamily: 'Mazzard, Mazzard H, Mazzard M, system-ui, sans-serif' }}>
              {t('quoteHistory')}: {selectedLead?.firstName} {selectedLead?.lastName}
            </DialogTitle>
          </DialogHeader>
          <div className="mt-4">
            {selectedLead && (
              <QuoteHistory 
                leadId={selectedLead.id} 
                vin={selectedLead.vin}
                onScenarioChange={() => fetchLeads()}
              />
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Wave 7 — Reassign dialog */}
      {canReassign && reassignTarget && (
        <ReassignDialog
          open={!!reassignTarget}
          onClose={() => setReassignTarget(null)}
          entity="lead"
          ids={reassignTarget.ids}
          currentManagerId={reassignTarget.currentManagerId}
          onSuccess={() => {
            setSelectedIds(new Set());
            invalidateManagers();
            fetchLeads();
          }}
        />
      )}
    </motion.div>
  );
};

export default Leads;

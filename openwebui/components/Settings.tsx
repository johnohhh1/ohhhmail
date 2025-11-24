/**
 * Settings Component - System configuration
 * Model selection, confidence thresholds, notifications, integrations
 */

import React, { useState, useEffect } from 'react';

interface ModelConfig {
  provider: 'ollama' | 'openai' | 'anthropic';
  model_name: string;
  api_key?: string;
  base_url?: string;
}

interface AgentModelConfig {
  triage: ModelConfig;
  vision: ModelConfig;
  deadline: ModelConfig;
  context: ModelConfig;
}

interface ThresholdConfig {
  high_confidence: number;
  medium_confidence: number;
  low_confidence: number;
  auto_process_threshold: number;
}

interface NotificationConfig {
  email_notifications: boolean;
  slack_notifications: boolean;
  webhook_url?: string;
  notify_on_high_confidence: boolean;
  notify_on_low_confidence: boolean;
  notify_on_errors: boolean;
}

interface IntegrationConfig {
  gmail_enabled: boolean;
  gmail_credentials?: string;
  calendar_sync: boolean;
  task_manager_integration: boolean;
  n8n_webhook_url?: string;
}

interface EmailFilterConfig {
  allowed_domains: string[];
  allowed_senders: string[];
  blocked_domains: string[];
  blocked_senders: string[];
  polling_interval: number;
}

interface SystemSettings {
  models: AgentModelConfig;
  thresholds: ThresholdConfig;
  notifications: NotificationConfig;
  integrations: IntegrationConfig;
  email_filter: EmailFilterConfig;
}

interface SettingsProps {
  className?: string;
}

export const Settings: React.FC<SettingsProps> = ({ className = '' }) => {
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'models' | 'thresholds' | 'notifications' | 'integrations' | 'email_filter'>(
    'email_filter'
  );
  const [availableModels, setAvailableModels] = useState<Record<string, string[]>>({
    ollama: [],
    openai: [],
    anthropic: [],
  });

  useEffect(() => {
    fetchSettings();
    fetchAvailableModels();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/settings');
      const data = await response.json();
      setSettings(data.settings);
      setIsLoading(false);
    } catch (error) {
      console.error('Failed to fetch settings:', error);
      setIsLoading(false);
    }
  };

  const fetchAvailableModels = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/models/available');
      const data = await response.json();
      setAvailableModels(data.models || { ollama: [], openai: [], anthropic: [] });
    } catch (error) {
      console.error('Failed to fetch available models:', error);
    }
  };

  const saveSettings = async () => {
    if (!settings) return;

    setIsSaving(true);
    try {
      await fetch('http://localhost:5000/api/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });
      alert('Settings saved successfully!');
    } catch (error) {
      console.error('Failed to save settings:', error);
      alert('Failed to save settings');
    } finally {
      setIsSaving(false);
    }
  };

  const updateAgentModel = (
    agent: keyof AgentModelConfig,
    field: keyof ModelConfig,
    value: string
  ) => {
    if (!settings) return;
    setSettings({
      ...settings,
      models: {
        ...settings.models,
        [agent]: {
          ...settings.models[agent],
          [field]: value,
        },
      },
    });
  };

  const updateThreshold = (field: keyof ThresholdConfig, value: number) => {
    if (!settings) return;
    setSettings({
      ...settings,
      thresholds: {
        ...settings.thresholds,
        [field]: value,
      },
    });
  };

  const updateNotification = (field: keyof NotificationConfig, value: boolean | string) => {
    if (!settings) return;
    setSettings({
      ...settings,
      notifications: {
        ...settings.notifications,
        [field]: value,
      },
    });
  };

  const updateIntegration = (field: keyof IntegrationConfig, value: boolean | string) => {
    if (!settings) return;
    setSettings({
      ...settings,
      integrations: {
        ...settings.integrations,
        [field]: value,
      },
    });
  };

  const updateEmailFilter = (field: keyof EmailFilterConfig, value: string[] | number) => {
    if (!settings) return;
    setSettings({
      ...settings,
      email_filter: {
        ...settings.email_filter,
        [field]: value,
      },
    });
  };

  const addEmailFilterItem = (field: 'allowed_domains' | 'allowed_senders' | 'blocked_domains' | 'blocked_senders', value: string) => {
    if (!settings || !value.trim()) return;
    const currentList = settings.email_filter[field];
    if (!currentList.includes(value.trim())) {
      updateEmailFilter(field, [...currentList, value.trim()]);
    }
  };

  const removeEmailFilterItem = (field: 'allowed_domains' | 'allowed_senders' | 'blocked_domains' | 'blocked_senders', value: string) => {
    if (!settings) return;
    updateEmailFilter(field, settings.email_filter[field].filter(item => item !== value));
  };

  if (isLoading || !settings) {
    return (
      <div className={`settings ${className} flex items-center justify-center h-full`}>
        <div className="text-gray-500">Loading settings...</div>
      </div>
    );
  }

  return (
    <div className={`settings ${className} h-full flex flex-col bg-gray-100`}>
      {/* Header */}
      <div className="p-4 bg-white shadow">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Settings</h2>
            <p className="text-sm text-gray-600 mt-1">Configure system preferences</p>
          </div>
          <button
            onClick={saveSettings}
            disabled={isSaving}
            className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
          >
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b">
        <div className="flex gap-1 px-4 overflow-x-auto">
          {[
            { key: 'email_filter', label: 'Email Filtering', icon: '📧' },
            { key: 'models', label: 'Models', icon: '🤖' },
            { key: 'thresholds', label: 'Thresholds', icon: '🎯' },
            { key: 'notifications', label: 'Notifications', icon: '🔔' },
            { key: 'integrations', label: 'Integrations', icon: '🔌' },
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`px-6 py-3 font-medium transition ${
                activeTab === tab.key
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 p-6 overflow-y-auto">
        {/* Email Filtering Tab */}
        {activeTab === 'email_filter' && (
          <div className="max-w-4xl">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Email Filtering (CRITICAL)</h3>
            <p className="text-gray-600 mb-6">
              Configure which email domains and senders are allowed or blocked. Only emails from allowed sources will be processed.
            </p>

            {/* Polling Interval */}
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Polling Interval: {settings.email_filter.polling_interval} seconds
              </label>
              <input
                type="range"
                min="30"
                max="300"
                step="30"
                value={settings.email_filter.polling_interval}
                onChange={(e) => updateEmailFilter('polling_interval', parseInt(e.target.value))}
                className="w-full"
              />
              <p className="text-sm text-gray-500 mt-1">
                How often to check for new emails (30 seconds to 5 minutes)
              </p>
            </div>

            {/* Allowed Domains */}
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <h4 className="text-lg font-semibold text-gray-800 mb-3">✅ Allowed Domains</h4>
              <p className="text-sm text-gray-600 mb-4">
                Only emails from these domains will be processed (e.g., chilis.com, brinker.com, hotschedules.com)
              </p>
              <div className="flex gap-2 mb-3">
                <input
                  type="text"
                  id="add-allowed-domain"
                  placeholder="Enter domain (e.g., chilis.com)"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      const input = e.target as HTMLInputElement;
                      addEmailFilterItem('allowed_domains', input.value);
                      input.value = '';
                    }
                  }}
                />
                <button
                  onClick={() => {
                    const input = document.getElementById('add-allowed-domain') as HTMLInputElement;
                    addEmailFilterItem('allowed_domains', input.value);
                    input.value = '';
                  }}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  Add
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {settings.email_filter.allowed_domains.map(domain => (
                  <div
                    key={domain}
                    className="flex items-center gap-2 px-3 py-1 bg-green-100 text-green-800 rounded-full"
                  >
                    <span className="text-sm">{domain}</span>
                    <button
                      onClick={() => removeEmailFilterItem('allowed_domains', domain)}
                      className="text-green-600 hover:text-green-800"
                    >
                      ✕
                    </button>
                  </div>
                ))}
                {settings.email_filter.allowed_domains.length === 0 && (
                  <p className="text-sm text-gray-500 italic">No domains configured - all emails allowed</p>
                )}
              </div>
            </div>

            {/* Allowed Senders */}
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <h4 className="text-lg font-semibold text-gray-800 mb-3">✅ Allowed Senders (Optional)</h4>
              <p className="text-sm text-gray-600 mb-4">
                If specified, only emails from these exact addresses will be processed (e.g., dm@chilis.com)
              </p>
              <div className="flex gap-2 mb-3">
                <input
                  type="email"
                  id="add-allowed-sender"
                  placeholder="Enter email address"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      const input = e.target as HTMLInputElement;
                      addEmailFilterItem('allowed_senders', input.value);
                      input.value = '';
                    }
                  }}
                />
                <button
                  onClick={() => {
                    const input = document.getElementById('add-allowed-sender') as HTMLInputElement;
                    addEmailFilterItem('allowed_senders', input.value);
                    input.value = '';
                  }}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  Add
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {settings.email_filter.allowed_senders.map(sender => (
                  <div
                    key={sender}
                    className="flex items-center gap-2 px-3 py-1 bg-green-100 text-green-800 rounded-full"
                  >
                    <span className="text-sm">{sender}</span>
                    <button
                      onClick={() => removeEmailFilterItem('allowed_senders', sender)}
                      className="text-green-600 hover:text-green-800"
                    >
                      ✕
                    </button>
                  </div>
                ))}
                {settings.email_filter.allowed_senders.length === 0 && (
                  <p className="text-sm text-gray-500 italic">Not configured - allows all senders from allowed domains</p>
                )}
              </div>
            </div>

            {/* Blocked Domains */}
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <h4 className="text-lg font-semibold text-gray-800 mb-3">🚫 Blocked Domains</h4>
              <p className="text-sm text-gray-600 mb-4">
                Emails from these domains will never be processed (e.g., spam.com, marketing.com)
              </p>
              <div className="flex gap-2 mb-3">
                <input
                  type="text"
                  id="add-blocked-domain"
                  placeholder="Enter domain to block"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      const input = e.target as HTMLInputElement;
                      addEmailFilterItem('blocked_domains', input.value);
                      input.value = '';
                    }
                  }}
                />
                <button
                  onClick={() => {
                    const input = document.getElementById('add-blocked-domain') as HTMLInputElement;
                    addEmailFilterItem('blocked_domains', input.value);
                    input.value = '';
                  }}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                >
                  Block
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {settings.email_filter.blocked_domains.map(domain => (
                  <div
                    key={domain}
                    className="flex items-center gap-2 px-3 py-1 bg-red-100 text-red-800 rounded-full"
                  >
                    <span className="text-sm">{domain}</span>
                    <button
                      onClick={() => removeEmailFilterItem('blocked_domains', domain)}
                      className="text-red-600 hover:text-red-800"
                    >
                      ✕
                    </button>
                  </div>
                ))}
                {settings.email_filter.blocked_domains.length === 0 && (
                  <p className="text-sm text-gray-500 italic">No blocked domains</p>
                )}
              </div>
            </div>

            {/* Blocked Senders */}
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <h4 className="text-lg font-semibold text-gray-800 mb-3">🚫 Blocked Senders</h4>
              <p className="text-sm text-gray-600 mb-4">
                Emails from these specific addresses will never be processed
              </p>
              <div className="flex gap-2 mb-3">
                <input
                  type="email"
                  id="add-blocked-sender"
                  placeholder="Enter email address to block"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      const input = e.target as HTMLInputElement;
                      addEmailFilterItem('blocked_senders', input.value);
                      input.value = '';
                    }
                  }}
                />
                <button
                  onClick={() => {
                    const input = document.getElementById('add-blocked-sender') as HTMLInputElement;
                    addEmailFilterItem('blocked_senders', input.value);
                    input.value = '';
                  }}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                >
                  Block
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {settings.email_filter.blocked_senders.map(sender => (
                  <div
                    key={sender}
                    className="flex items-center gap-2 px-3 py-1 bg-red-100 text-red-800 rounded-full"
                  >
                    <span className="text-sm">{sender}</span>
                    <button
                      onClick={() => removeEmailFilterItem('blocked_senders', sender)}
                      className="text-red-600 hover:text-red-800"
                    >
                      ✕
                    </button>
                  </div>
                ))}
                {settings.email_filter.blocked_senders.length === 0 && (
                  <p className="text-sm text-gray-500 italic">No blocked senders</p>
                )}
              </div>
            </div>

            {/* Current Configuration Summary */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-semibold text-blue-900 mb-2">📋 Current Configuration</h4>
              <div className="text-sm text-blue-800 space-y-1">
                <p>• Allowed Domains: {settings.email_filter.allowed_domains.length || 'All domains'}</p>
                <p>• Allowed Senders: {settings.email_filter.allowed_senders.length || 'All senders from allowed domains'}</p>
                <p>• Blocked Domains: {settings.email_filter.blocked_domains.length || 'None'}</p>
                <p>• Blocked Senders: {settings.email_filter.blocked_senders.length || 'None'}</p>
                <p>• Polling every {settings.email_filter.polling_interval} seconds</p>
              </div>
            </div>
          </div>
        )}

        {/* Models Tab */}
        {activeTab === 'models' && (
          <div className="max-w-4xl">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Agent Model Configuration</h3>
            <p className="text-gray-600 mb-6">
              Configure which AI models each agent uses. You can swap between GPT, Claude, and Ollama.
            </p>

            <div className="space-y-6">
              {Object.entries(settings.models).map(([agent, config]) => (
                <div key={agent} className="bg-white rounded-lg shadow p-6">
                  <h4 className="text-lg font-semibold text-gray-800 capitalize mb-4">
                    {agent} Agent
                  </h4>

                  <div className="grid grid-cols-2 gap-4">
                    {/* Provider Selection */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Provider
                      </label>
                      <select
                        value={config.provider}
                        onChange={(e) =>
                          updateAgentModel(agent as keyof AgentModelConfig, 'provider', e.target.value)
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="ollama">Ollama (Local)</option>
                        <option value="openai">OpenAI (GPT)</option>
                        <option value="anthropic">Anthropic (Claude)</option>
                      </select>
                    </div>

                    {/* Model Selection */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Model
                      </label>
                      <select
                        value={config.model_name}
                        onChange={(e) =>
                          updateAgentModel(agent as keyof AgentModelConfig, 'model_name', e.target.value)
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      >
                        {availableModels[config.provider]?.map(model => (
                          <option key={model} value={model}>
                            {model}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* API Key (for non-Ollama) */}
                    {config.provider !== 'ollama' && (
                      <div className="col-span-2">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          API Key
                        </label>
                        <input
                          type="password"
                          value={config.api_key || ''}
                          onChange={(e) =>
                            updateAgentModel(agent as keyof AgentModelConfig, 'api_key', e.target.value)
                          }
                          placeholder="sk-..."
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    )}

                    {/* Base URL (optional) */}
                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Base URL (optional)
                      </label>
                      <input
                        type="text"
                        value={config.base_url || ''}
                        onChange={(e) =>
                          updateAgentModel(agent as keyof AgentModelConfig, 'base_url', e.target.value)
                        }
                        placeholder="http://localhost:11434"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Thresholds Tab */}
        {activeTab === 'thresholds' && (
          <div className="max-w-4xl">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Confidence Thresholds</h3>
            <p className="text-gray-600 mb-6">
              Configure confidence thresholds for automatic processing and alerts.
            </p>

            <div className="bg-white rounded-lg shadow p-6 space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  High Confidence Threshold: {(settings.thresholds.high_confidence * 100).toFixed(0)}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={settings.thresholds.high_confidence * 100}
                  onChange={(e) => updateThreshold('high_confidence', parseInt(e.target.value) / 100)}
                  className="w-full"
                />
                <p className="text-sm text-gray-500 mt-1">
                  Actions above this threshold are automatically processed
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Medium Confidence Threshold: {(settings.thresholds.medium_confidence * 100).toFixed(0)}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={settings.thresholds.medium_confidence * 100}
                  onChange={(e) => updateThreshold('medium_confidence', parseInt(e.target.value) / 100)}
                  className="w-full"
                />
                <p className="text-sm text-gray-500 mt-1">
                  Actions in this range require confirmation
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Low Confidence Threshold: {(settings.thresholds.low_confidence * 100).toFixed(0)}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={settings.thresholds.low_confidence * 100}
                  onChange={(e) => updateThreshold('low_confidence', parseInt(e.target.value) / 100)}
                  className="w-full"
                />
                <p className="text-sm text-gray-500 mt-1">
                  Actions below this are flagged for manual review
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Auto-Process Threshold: {(settings.thresholds.auto_process_threshold * 100).toFixed(0)}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={settings.thresholds.auto_process_threshold * 100}
                  onChange={(e) =>
                    updateThreshold('auto_process_threshold', parseInt(e.target.value) / 100)
                  }
                  className="w-full"
                />
                <p className="text-sm text-gray-500 mt-1">
                  Minimum confidence to process emails without human review
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Notifications Tab */}
        {activeTab === 'notifications' && (
          <div className="max-w-4xl">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Notification Preferences</h3>
            <p className="text-gray-600 mb-6">
              Configure when and how you receive notifications.
            </p>

            <div className="bg-white rounded-lg shadow p-6 space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-800">Email Notifications</p>
                  <p className="text-sm text-gray-500">Receive notifications via email</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.notifications.email_notifications}
                    onChange={(e) => updateNotification('email_notifications', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-800">Slack Notifications</p>
                  <p className="text-sm text-gray-500">Send notifications to Slack</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.notifications.slack_notifications}
                    onChange={(e) => updateNotification('slack_notifications', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Webhook URL
                </label>
                <input
                  type="text"
                  value={settings.notifications.webhook_url || ''}
                  onChange={(e) => updateNotification('webhook_url', e.target.value)}
                  placeholder="https://hooks.slack.com/services/..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="border-t pt-4">
                <p className="font-medium text-gray-800 mb-3">Notification Triggers</p>
                <div className="space-y-3">
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={settings.notifications.notify_on_high_confidence}
                      onChange={(e) =>
                        updateNotification('notify_on_high_confidence', e.target.checked)
                      }
                      className="w-4 h-4"
                    />
                    <span className="text-sm text-gray-700">High confidence detections</span>
                  </label>
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={settings.notifications.notify_on_low_confidence}
                      onChange={(e) => updateNotification('notify_on_low_confidence', e.target.checked)}
                      className="w-4 h-4"
                    />
                    <span className="text-sm text-gray-700">Low confidence requiring review</span>
                  </label>
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={settings.notifications.notify_on_errors}
                      onChange={(e) => updateNotification('notify_on_errors', e.target.checked)}
                      className="w-4 h-4"
                    />
                    <span className="text-sm text-gray-700">Processing errors</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Integrations Tab */}
        {activeTab === 'integrations' && (
          <div className="max-w-4xl">
            <h3 className="text-xl font-bold text-gray-800 mb-4">External Integrations</h3>
            <p className="text-gray-600 mb-6">
              Connect ohhhmail with external services.
            </p>

            <div className="space-y-6">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <p className="font-medium text-gray-800">Gmail Integration</p>
                    <p className="text-sm text-gray-500">Sync emails from Gmail</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.integrations.gmail_enabled}
                      onChange={(e) => updateIntegration('gmail_enabled', e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
                {settings.integrations.gmail_enabled && (
                  <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                    Configure Gmail OAuth
                  </button>
                )}
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-800">Calendar Sync</p>
                    <p className="text-sm text-gray-500">Sync events to Google Calendar</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.integrations.calendar_sync}
                      onChange={(e) => updateIntegration('calendar_sync', e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-800">Task Manager Integration</p>
                    <p className="text-sm text-gray-500">Create tasks in external system</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.integrations.task_manager_integration}
                      onChange={(e) => updateIntegration('task_manager_integration', e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  n8n Webhook URL
                </label>
                <input
                  type="text"
                  value={settings.integrations.n8n_webhook_url || ''}
                  onChange={(e) => updateIntegration('n8n_webhook_url', e.target.value)}
                  placeholder="https://your-n8n-instance.com/webhook/..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-sm text-gray-500 mt-1">
                  Send processed emails to n8n workflow
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

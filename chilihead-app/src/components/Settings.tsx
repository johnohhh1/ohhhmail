'use client';

import { useState, useEffect } from 'react';

interface EmailFilterConfig {
  allowed_domains: string[];
  allowed_senders: string[];
  blocked_domains: string[];
  blocked_senders: string[];
  polling_interval: number;
}

export default function Settings() {
  const [settings, setSettings] = useState<EmailFilterConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [newDomain, setNewDomain] = useState('');
  const [newSender, setNewSender] = useState('');

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/settings');
      const data = await response.json();
      setSettings(data);
    } catch (error) {
      console.error('Failed to fetch settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    if (!settings) return;
    setSaving(true);

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
      setSaving(false);
    }
  };

  const addItem = (field: keyof EmailFilterConfig, value: string) => {
    if (!settings || !value.trim()) return;
    const list = settings[field] as string[];
    if (!list.includes(value.trim())) {
      setSettings({
        ...settings,
        [field]: [...list, value.trim()],
      });
    }
  };

  const removeItem = (field: keyof EmailFilterConfig, value: string) => {
    if (!settings) return;
    const list = settings[field] as string[];
    setSettings({
      ...settings,
      [field]: list.filter((item) => item !== value),
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-600">Loading settings...</div>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-red-600">Failed to load settings</div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto bg-gray-100">
      <div className="max-w-4xl mx-auto p-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Email Filter Settings</h2>

          {/* Allowed Domains */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              Allowed Domains
            </h3>
            <p className="text-sm text-gray-600 mb-3">
              Only process emails from these domains (e.g., chilis.com, brinker.com)
            </p>
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={newDomain}
                onChange={(e) => setNewDomain(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    addItem('allowed_domains', newDomain);
                    setNewDomain('');
                  }
                }}
                placeholder="example.com"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={() => {
                  addItem('allowed_domains', newDomain);
                  setNewDomain('');
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {settings.allowed_domains.map((domain) => (
                <span
                  key={domain}
                  className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm flex items-center gap-2"
                >
                  {domain}
                  <button
                    onClick={() => removeItem('allowed_domains', domain)}
                    className="text-green-600 hover:text-green-800"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Blocked Domains */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              Blocked Domains
            </h3>
            <p className="text-sm text-gray-600 mb-3">
              Never process emails from these domains
            </p>
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={newDomain}
                onChange={(e) => setNewDomain(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    addItem('blocked_domains', newDomain);
                    setNewDomain('');
                  }
                }}
                placeholder="spam.com"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={() => {
                  addItem('blocked_domains', newDomain);
                  setNewDomain('');
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {settings.blocked_domains.map((domain) => (
                <span
                  key={domain}
                  className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm flex items-center gap-2"
                >
                  {domain}
                  <button
                    onClick={() => removeItem('blocked_domains', domain)}
                    className="text-red-600 hover:text-red-800"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Polling Interval */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              Email Polling Interval
            </h3>
            <p className="text-sm text-gray-600 mb-3">
              How often to check for new emails (in seconds)
            </p>
            <input
              type="number"
              value={settings.polling_interval}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  polling_interval: parseInt(e.target.value) || 60,
                })
              }
              min="30"
              max="3600"
              className="w-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-600">seconds</span>
          </div>

          {/* Save Button */}
          <div className="pt-6 border-t border-gray-200">
            <button
              onClick={saveSettings}
              disabled={saving}
              className="px-6 py-3 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
            >
              {saving ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

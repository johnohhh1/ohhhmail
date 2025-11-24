// ChiliHead OpsManager v2.1 - Custom Tab Integration for Open-WebUI

(function() {
  'use strict';

  // Wait for DOM to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initChiliHead);
  } else {
    initChiliHead();
  }

  function initChiliHead() {
    console.log('🌶️ ChiliHead OpsManager v2.1 - Initializing...');

    // Add custom tabs to Open-WebUI navigation
    addCustomTabs();

    // Add custom styles
    addCustomStyles();

    console.log('✅ ChiliHead OpsManager initialized');
  }

  function addCustomTabs() {
    // Find the main navigation or sidebar
    const nav = document.querySelector('nav') || document.querySelector('[role="navigation"]');

    if (!nav) {
      console.warn('Navigation element not found, retrying in 1s...');
      setTimeout(addCustomTabs, 1000);
      return;
    }

    // Create Email tab
    const emailTab = createTab({
      id: 'chilihead-email',
      icon: '📧',
      label: 'Email Client',
      content: createEmailClient()
    });

    // Create Settings tab
    const settingsTab = createTab({
      id: 'chilihead-settings',
      icon: '⚙️',
      label: 'Settings',
      content: createSettingsPanel()
    });

    // Inject tabs into navigation
    nav.appendChild(emailTab);
    nav.appendChild(settingsTab);
  }

  function createTab({ id, icon, label, content }) {
    const tab = document.createElement('div');
    tab.className = 'chilihead-tab';
    tab.id = id;
    tab.innerHTML = `
      <button class="chilihead-tab-btn" onclick="window.ChiliHead.switchTab('${id}')">
        <span class="tab-icon">${icon}</span>
        <span class="tab-label">${label}</span>
      </button>
      <div class="chilihead-tab-content" id="${id}-content" style="display: none;">
        ${content}
      </div>
    `;
    return tab;
  }

  function createEmailClient() {
    return `
      <div class="chilihead-email-client">
        <iframe
          src="http://localhost:8888"
          class="chilihead-iframe"
          allow="clipboard-read; clipboard-write"
          title="SnappyMail Email Client">
        </iframe>
      </div>
    `;
  }

  function createSettingsPanel() {
    return `
      <div class="chilihead-settings">
        <div class="settings-container">
          <h2 class="settings-title">📧 Email Filter Settings</h2>

          <div class="settings-section">
            <h3>Allowed Domains</h3>
            <p class="settings-description">Only process emails from these domains</p>
            <div class="domain-list">
              <span class="domain-tag allowed">chilis.com</span>
              <span class="domain-tag allowed">brinker.com</span>
              <span class="domain-tag allowed">hotschedules.com</span>
            </div>
            <input type="text" id="add-allowed-domain" placeholder="Add domain..." class="domain-input">
            <button onclick="window.ChiliHead.addDomain('allowed')" class="btn-add">Add Domain</button>
          </div>

          <div class="settings-section">
            <h3>Blocked Domains</h3>
            <p class="settings-description">Never process emails from these domains</p>
            <div class="domain-list">
              <span class="domain-tag blocked">spam.com</span>
              <span class="domain-tag blocked">marketing.com</span>
            </div>
            <input type="text" id="add-blocked-domain" placeholder="Add domain..." class="domain-input">
            <button onclick="window.ChiliHead.addDomain('blocked')" class="btn-add">Add Domain</button>
          </div>

          <div class="settings-actions">
            <button onclick="window.ChiliHead.saveSettings()" class="btn-save">💾 Save Settings</button>
          </div>
        </div>
      </div>
    `;
  }

  function addCustomStyles() {
    const style = document.createElement('style');
    style.textContent = `
      .chilihead-tab-btn {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem 1.5rem;
        background: transparent;
        border: none;
        color: #9ca3af;
        cursor: pointer;
        font-size: 0.875rem;
        font-weight: 500;
        transition: all 0.2s;
      }

      .chilihead-tab-btn:hover {
        color: #e5e7eb;
        background: rgba(75, 85, 99, 0.5);
      }

      .chilihead-tab-btn.active {
        color: #fff;
        background: #1f2937;
        border-top: 2px solid #3b82f6;
      }

      .chilihead-tab-content {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: #111827;
        z-index: 9999;
      }

      .chilihead-iframe {
        width: 100%;
        height: 100%;
        border: none;
      }

      .chilihead-settings {
        width: 100%;
        height: 100%;
        overflow-y: auto;
        background: #f3f4f6;
        padding: 2rem;
      }

      .settings-container {
        max-width: 800px;
        margin: 0 auto;
        background: white;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        padding: 2rem;
      }

      .settings-title {
        font-size: 1.5rem;
        font-weight: bold;
        color: #111827;
        margin-bottom: 1.5rem;
      }

      .settings-section {
        margin-bottom: 2rem;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid #e5e7eb;
      }

      .settings-section h3 {
        font-size: 1.125rem;
        font-weight: 600;
        color: #374151;
        margin-bottom: 0.5rem;
      }

      .settings-description {
        font-size: 0.875rem;
        color: #6b7280;
        margin-bottom: 1rem;
      }

      .domain-list {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 1rem;
      }

      .domain-tag {
        padding: 0.5rem 1rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 500;
      }

      .domain-tag.allowed {
        background: #d1fae5;
        color: #065f46;
      }

      .domain-tag.blocked {
        background: #fee2e2;
        color: #991b1b;
      }

      .domain-input {
        padding: 0.5rem 1rem;
        border: 1px solid #d1d5db;
        border-radius: 0.375rem;
        font-size: 0.875rem;
        margin-right: 0.5rem;
        width: 300px;
      }

      .btn-add, .btn-save {
        padding: 0.5rem 1.5rem;
        border: none;
        border-radius: 0.375rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
      }

      .btn-add {
        background: #3b82f6;
        color: white;
      }

      .btn-add:hover {
        background: #2563eb;
      }

      .btn-save {
        background: #10b981;
        color: white;
        font-size: 1rem;
      }

      .btn-save:hover {
        background: #059669;
      }

      .settings-actions {
        margin-top: 2rem;
        padding-top: 1.5rem;
        border-top: 1px solid #e5e7eb;
      }
    `;
    document.head.appendChild(style);
  }

  // Global ChiliHead API
  window.ChiliHead = {
    switchTab: function(tabId) {
      // Hide all tab contents
      document.querySelectorAll('.chilihead-tab-content').forEach(el => {
        el.style.display = 'none';
      });

      // Remove active class from all buttons
      document.querySelectorAll('.chilihead-tab-btn').forEach(el => {
        el.classList.remove('active');
      });

      // Show selected tab
      const content = document.getElementById(tabId + '-content');
      if (content) {
        content.style.display = 'block';
      }

      // Activate button
      const button = document.querySelector(`#${tabId} .chilihead-tab-btn`);
      if (button) {
        button.classList.add('active');
      }
    },

    addDomain: function(type) {
      const input = document.getElementById(`add-${type}-domain`);
      const domain = input.value.trim();

      if (!domain) return;

      // Create new domain tag
      const tag = document.createElement('span');
      tag.className = `domain-tag ${type}`;
      tag.textContent = domain;

      // Add to list
      const list = document.querySelector(`#chilihead-settings .settings-section:nth-child(${type === 'allowed' ? '1' : '2'}) .domain-list`);
      list.appendChild(tag);

      // Clear input
      input.value = '';
    },

    saveSettings: async function() {
      // Collect all domains
      const allowedDomains = Array.from(document.querySelectorAll('.domain-tag.allowed'))
        .map(el => el.textContent);
      const blockedDomains = Array.from(document.querySelectorAll('.domain-tag.blocked'))
        .map(el => el.textContent);

      // Save to backend
      try {
        const response = await fetch('/api/chilihead/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            allowed_domains: allowedDomains,
            blocked_domains: blockedDomains
          })
        });

        if (response.ok) {
          alert('✅ Settings saved successfully!');
        } else {
          alert('❌ Failed to save settings');
        }
      } catch (error) {
        console.error('Error saving settings:', error);
        alert('❌ Error saving settings');
      }
    }
  };
})();

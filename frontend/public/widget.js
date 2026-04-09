/**
 * PropVision.AI — Embeddable Widget Script
 *
 * Usage:
 * <div id="propvision-widget"
 *   data-api-key="pv_live_xxx"
 *   data-property-id="uuid"
 *   data-theme="light|dark"
 *   data-height="600px"
 * ></div>
 * <script src="https://api.propvision.ai/widget.js" async></script>
 */

(function() {
  'use strict';

  // Configuration
  var WIDGET_BASE_URL = 'https://app.propvision.ai';

  function init() {
    var containers = document.querySelectorAll('[id="propvision-widget"]');
    
    containers.forEach(function(container) {
      var apiKey = container.getAttribute('data-api-key');
      var propertyId = container.getAttribute('data-property-id');
      var theme = container.getAttribute('data-theme') || 'dark';
      var height = container.getAttribute('data-height') || '600px';
      var showScores = container.getAttribute('data-show-scores') !== 'false';
      var show3D = container.getAttribute('data-show-3d') !== 'false';
      var locale = container.getAttribute('data-locale') || 'en';

      if (!apiKey || !propertyId) {
        console.error('[PropVision] Missing required attributes: data-api-key and data-property-id');
        return;
      }

      // Create iframe
      var iframe = document.createElement('iframe');
      var params = new URLSearchParams({
        apiKey: apiKey,
        propertyId: propertyId,
        theme: theme,
        showScores: showScores.toString(),
        show3D: show3D.toString(),
        locale: locale,
        widget: 'true',
      });

      iframe.src = WIDGET_BASE_URL + '/widget?' + params.toString();
      iframe.style.width = '100%';
      iframe.style.height = height;
      iframe.style.border = 'none';
      iframe.style.borderRadius = '12px';
      iframe.style.overflow = 'hidden';
      iframe.setAttribute('loading', 'lazy');
      iframe.setAttribute('allow', 'fullscreen; webgl');
      iframe.setAttribute('title', 'PropVision Property Viewer');

      // Clear container and insert iframe
      container.innerHTML = '';
      container.appendChild(iframe);

      // Listen for resize messages from the iframe
      window.addEventListener('message', function(event) {
        if (event.data && event.data.type === 'propvision:resize') {
          iframe.style.height = event.data.height + 'px';
        }
      });
    });
  }

  // Listen for dynamic property updates
  window.addEventListener('message', function(event) {
    if (event.data && event.data.type === 'propvision:update') {
      var iframe = document.querySelector('#propvision-widget iframe');
      if (iframe && event.data.propertyId) {
        var url = new URL(iframe.src);
        url.searchParams.set('propertyId', event.data.propertyId);
        iframe.src = url.toString();
      }
    }
  });

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

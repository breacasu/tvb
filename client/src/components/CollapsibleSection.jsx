import React, { useState } from 'react';

function CollapsibleSection({ title, defaultOpen, children }) {
  const [open, setOpen] = useState(defaultOpen !== false);

  return (
    <div className={`collapsible-section ${open ? 'open' : 'closed'}`}>
      <div className="collapsible-header" onClick={() => setOpen(!open)}>
        <span className="collapsible-arrow">{open ? '▾' : '▸'}</span>
        <span className="collapsible-title">{title}</span>
      </div>
      {open && <div className="collapsible-body">{children}</div>}
    </div>
  );
}

export default CollapsibleSection;
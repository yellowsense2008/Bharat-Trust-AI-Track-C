# Frontend Requirements Document
## Bharat Trust AI - Track C Grievance System

**Version**: 1.0  
**Date**: January 2025  
**For**: Frontend Development Team  
**Backend API**: [Your Cloud Run URL]

---

## 1. CITIZEN INTERFACE (Mobile-First)

### 1.1 Voice Complaint Filing Screen

**Purpose**: Allow citizens to file complaints via voice conversation

**Components**:
- Large microphone button (center of screen)
- Voice waveform animation during recording
- Real-time transcription display
- AI response text-to-speech playback
- Language selector (English, Hindi, Tamil, Gujarati, etc.)

**API Integration**:
```
POST /voice/transcribe
- Input: Audio file (WAV/MP3)
- Output: {"transcription": "text"}

POST /conversation/start
- Input: {"message": "transcribed_text"}
- Output: {"ai_response": "...", "conversation_complete": false}

POST /conversation/message
- Input: {"message": "user_response"}
- Output: {"ai_response": "...", "conversation_complete": true/false}

POST /voice/synthesize
- Input: {"text": "ai_response", "language": "hi"}
- Output: Audio file
```

**User Flow**:
1. User taps microphone → Records voice
2. System transcribes → Shows text
3. AI responds → Plays voice response
4. Repeat until complaint complete
5. Show reference ID: "GRV-2026-XXXX"

**UI Elements**:
- 🎤 Record button (red when active)
- 📝 Transcription box (scrollable)
- 🔊 Speaker icon (AI speaking)
- ✅ Confirmation dialog before submission
- 📋 Reference ID display (large, copyable)

---

### 1.2 Text-Based Complaint Filing (Alternative)

**Purpose**: For users who prefer typing

**Components**:
- Chat interface (WhatsApp-style)
- User messages (right-aligned, blue)
- AI messages (left-aligned, gray)
- Input text box with send button
- Bank selection dropdown
- Form field indicators (progress bar)

**API Integration**:
```
POST /conversation/start
POST /conversation/message
```

**UI Elements**:
- Chat bubbles with timestamps
- Typing indicator when AI is processing
- Progress indicator (4/7 fields collected)
- Confirmation summary card
- Submit button (green)

---

### 1.3 Complaint Status Tracking

**Purpose**: Check complaint resolution status

**Components**:
- Reference ID input field
- Search button
- Status timeline (vertical)
- Resolution display (simplified)
- Download resolution button

**API Integration**:
```
GET /complaints/{reference_id}/resolution
- Output: {
  "reference_id": "GRV-2026-0009",
  "resolution": "Your bank will investigate...",
  "status": "action_in_progress"
}
```

**Status Display**:
- `submitted` → 🔵 Submitted
- `categorized` → 🟡 Under Review
- `action_in_progress` → 🟠 Bank Processing
- `resolved` → 🟢 Resolved

**UI Elements**:
- Timeline with checkmarks
- Estimated completion date
- Resolution text (large, readable)
- Share button (WhatsApp, SMS)

---

### 1.4 Multilingual Support

**Languages**: English, Hindi, Tamil, Gujarati, Bengali, Marathi, Punjabi

**Implementation**:
- Language selector on home screen
- All UI text in selected language
- Voice input/output in selected language
- Auto-detect language from voice input

---

## 2. ADMIN DASHBOARD (Desktop)

### 2.1 Complaints List View

**Purpose**: View all complaints with filters

**Components**:
- Data table (sortable columns)
- Filters: Status, Department, Priority, Date Range
- Search by reference ID or keywords
- Pagination (50 per page)
- Export to CSV button

**API Integration**:
```
GET /admin/complaints
- Headers: Authorization: Bearer {admin_token}
- Output: Array of complaints
```

**Table Columns**:
- Reference ID (clickable)
- Title
- Status (badge with color)
- Priority (1-10, color-coded)
- Department
- Created Date
- Actions (View, Edit)

**Filters**:
- Status dropdown
- Department dropdown
- Priority range slider
- Date picker (from/to)

---

### 2.2 Complaint Detail View

**Purpose**: View full complaint details and AI analysis

**Components**:
- Complaint header (reference ID, status, priority)
- Customer details card
- Transaction details card
- AI analysis section
- Resolution section
- Action buttons

**API Integration**:
```
GET /admin/complaints/{complaint_id}
GET /admin/complaints/{complaint_id}/ai-resolution
```

**Sections**:

**A. Complaint Header**
- Reference ID (large)
- Status badge
- Priority score (1-10 with color)
- Created date
- Last updated

**B. Customer Details**
- Name
- Mobile number
- Bank name

**C. Transaction Details**
- Transaction type
- Amount
- Date
- Transaction ID
- Description

**D. AI Analysis**
- Category (badge)
- Confidence score (%)
- Assigned department
- Duplicate detection (if any)

**E. AI Resolution**
- Suggested resolution (full text)
- Timeline breakdown
- Regulatory references
- Confidence score
- Similar cases count

**F. Action Buttons**
- 🤖 Generate AI Resolution
- ✅ Approve Resolution
- ✏️ Edit Resolution
- 📝 Update Status
- 🗑️ Close Complaint

---

### 2.3 AI Resolution Generation

**Purpose**: Generate and approve AI resolutions

**Components**:
- Generate button
- Loading spinner
- Resolution preview (full detail)
- Edit textarea (if admin wants to modify)
- Approve button
- Reject button

**API Integration**:
```
GET /admin/complaints/{complaint_id}/ai-resolution
- Output: {
  "ai_resolution": {
    "suggested_resolution": "...",
    "confidence": 0.85,
    "timeline": "...",
    "regulatory_reference": "..."
  }
}

POST /admin/complaints/{complaint_id}/approve-resolution
- Output: {
  "message": "Resolution approved",
  "status": "action_in_progress"
}
```

**UI Flow**:
1. Admin clicks "Generate AI Resolution"
2. Loading spinner (2-3 seconds)
3. Show full resolution with:
   - Main resolution text
   - Timeline (3-10 days)
   - Regulatory references
   - Confidence score
4. Admin reviews
5. Admin clicks "Approve" or "Edit"
6. Status changes to "action_in_progress"

---

### 2.4 Dashboard Analytics

**Purpose**: Overview of complaint statistics

**Components**:
- KPI cards (4 cards in row)
- Charts (bar, line, pie)
- Recent complaints table
- Priority distribution
- Department workload

**API Integration**:
```
GET /admin/analytics/summary
GET /admin/analytics/trends
```

**KPI Cards**:
- Total Complaints (number)
- Pending Resolution (number, red)
- Resolved Today (number, green)
- Average Resolution Time (days)

**Charts**:
- Complaints by Status (pie chart)
- Complaints Over Time (line chart)
- Department Workload (bar chart)
- Priority Distribution (donut chart)

---

### 2.5 Complaint Update Form

**Purpose**: Admin can update complaint details

**Components**:
- Status dropdown
- Department dropdown
- Priority slider (1-10)
- Resolution textarea
- Save button

**API Integration**:
```
PATCH /admin/complaints/{complaint_id}
- Input: {
  "status": "IN_PROGRESS",
  "resolution": "Updated resolution text",
  "assigned_department": "Banking Operations",
  "priority_score": 8
}
```

---

## 3. AUTHENTICATION

### 3.1 Login Screen

**Components**:
- Email input
- Password input
- Login button
- "Forgot Password" link
- Role indicator (Citizen/Admin)

**API Integration**:
```
POST /auth/login
- Input: username (email), password (form-data)
- Output: {"access_token": "...", "token_type": "bearer"}
```

**Store token in**:
- LocalStorage (web)
- SecureStorage (mobile)

---

### 3.2 Registration Screen (Citizen Only)

**Components**:
- Name input
- Email input
- Password input
- Confirm password input
- Register button

**API Integration**:
```
POST /auth/register
- Input: {
  "name": "...",
  "email": "...",
  "password": "...",
  "role": "citizen"
}
```

---

## 4. TECHNICAL SPECIFICATIONS

### 4.1 API Base URL
```
Production: https://your-app.run.app
Development: http://localhost:8000
```

### 4.2 Authentication
All protected endpoints require:
```
Headers: {
  "Authorization": "Bearer {access_token}"
}
```

### 4.3 Error Handling
```json
{
  "detail": "Error message"
}
```

Display user-friendly error messages:
- 401 → "Please login again"
- 403 → "Access denied"
- 404 → "Not found"
- 500 → "Something went wrong. Please try again."

### 4.4 Loading States
- Show spinner during API calls
- Disable buttons during submission
- Show progress indicators for multi-step flows

### 4.5 Responsive Design
- Mobile-first for citizen interface
- Desktop-optimized for admin dashboard
- Tablet support for both

---

## 5. DESIGN GUIDELINES

### 5.1 Color Scheme
- Primary: #1976D2 (Blue)
- Success: #4CAF50 (Green)
- Warning: #FF9800 (Orange)
- Error: #F44336 (Red)
- Info: #2196F3 (Light Blue)

### 5.2 Typography
- Headings: Roboto Bold
- Body: Roboto Regular
- Monospace (Reference IDs): Roboto Mono

### 5.3 Icons
Use Material Icons or Font Awesome:
- 🎤 Microphone
- 📋 Clipboard
- ✅ Check
- ❌ Close
- 🔍 Search
- 📊 Analytics

### 5.4 Accessibility
- High contrast text
- Large touch targets (48x48px minimum)
- Screen reader support
- Keyboard navigation (admin dashboard)

---

## 6. PRIORITY FEATURES

### Phase 1 (MVP - 2 weeks)
1. ✅ Citizen voice complaint filing
2. ✅ Complaint status tracking
3. ✅ Admin complaints list
4. ✅ Admin complaint detail view
5. ✅ AI resolution approval

### Phase 2 (Enhancement - 1 week)
1. Text-based complaint filing
2. Dashboard analytics
3. Complaint update form
4. Export functionality

### Phase 3 (Polish - 1 week)
1. Multilingual UI
2. Advanced filters
3. Notifications
4. Mobile app optimization

---

## 7. API ENDPOINTS SUMMARY

### Citizen Endpoints (No Auth Required)
```
GET  /complaints/{reference_id}/resolution
```

### Citizen Endpoints (Auth Required)
```
POST /conversation/start
POST /conversation/message
POST /voice/transcribe
POST /voice/synthesize
```

### Admin Endpoints (Admin Auth Required)
```
GET    /admin/complaints
GET    /admin/complaints/{id}
GET    /admin/complaints/{id}/ai-resolution
POST   /admin/complaints/{id}/approve-resolution
PATCH  /admin/complaints/{id}
```

### Auth Endpoints
```
POST /auth/register
POST /auth/login
```

---

## 8. TESTING CHECKLIST

### Citizen Interface
- [ ] Voice recording works on mobile
- [ ] Audio playback works
- [ ] Conversation flow completes
- [ ] Reference ID is displayed
- [ ] Status tracking works
- [ ] Works in Hindi/Tamil/Gujarati

### Admin Dashboard
- [ ] Login works
- [ ] Complaints list loads
- [ ] Filters work
- [ ] Complaint detail shows all data
- [ ] AI resolution generation works
- [ ] Approval changes status
- [ ] Update form saves changes

---

## 9. DEPLOYMENT NOTES

### Environment Variables (Frontend)
```
REACT_APP_API_URL=https://your-app.run.app
REACT_APP_ENV=production
```

### CORS
Backend already configured to allow all origins:
```python
allow_origins=["*"]
```

---

## 10. SUPPORT & CONTACT

**Backend Developer**: [Your Name]  
**API Documentation**: https://your-app.run.app/docs  
**GitHub**: https://github.com/yellowsense2008/bharat-trust-ai-track-c  

---

**End of Requirements Document**

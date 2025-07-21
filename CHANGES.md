# Dashboard Changes - Functional/Operational

## Overview
This document tracks functional and operational changes needed for the Account Analysis dashboard.

## Changes to Implement

### High Priority - Core Functionality
- [x] **Go Live with Real Data**: Replace mock data with real database connections on all pages
  - **Location**: API endpoints, database connections
  - **Details**: Connect to actual database instead of mock data
  - **Priority**: High
  - **Status**: ✅ Completed - Created `/dev/live-data` endpoint that connects to real database with fallback to mock data

- [ ] **Authentication & Authorization**: Implement proper auth functionality
  - **Location**: Auth system, user management
  - **Details**: Install and configure auth Z functionality
  - **Priority**: High

- [ ] **Monthly Update Tool**: Create data import/upload functionality
  - **Location**: ETL system, file upload endpoints
  - **Details**: Import Sample data (HT), Expense (LG), Collectors (LG), Account Match (RL)
  - **Priority**: High

### Medium Priority - UI/UX Improvements
- [ ] **Color Scheme Update**: Change blue badge to green
  - **Location**: CSS/styling files
  - **Details**: Update badge colors from blue to green
  - **Priority**: Medium

- [ ] **Hi/Lo Sorting**: Sort on Net Income instead of current metric
  - **Location**: Dashboard sorting logic
  - **Details**: Change Hi/Lo to sort by Net Income
  - **Priority**: Medium

- [ ] **Account Hiding Feature**: Create "What if" scenarios by hiding accounts
  - **Location**: Dashboard interface, data filtering
  - **Details**: Allow users to hide accounts to see how metrics are affected
  - **Priority**: Medium

- [ ] **Tool Tips**: Add tooltips for all columns and metrics
  - **Location**: Dashboard HTML/JavaScript
  - **Details**: Implement hover tooltips for better user experience
  - **Priority**: Medium

- [ ] **Reset Button Styling**: Change reset from button to link or distinguish it
  - **Location**: Dashboard interface
  - **Details**: Make reset less prominent than action buttons
  - **Priority**: Medium

- [ ] **Data Alignment**: Align right the samples column data
  - **Location**: Dashboard table styling
  - **Details**: Right-align sample column data for better readability
  - **Priority**: Medium

- [ ] **Yellow Box Alignment**: Align new accounts count box with data
  - **Location**: Dashboard layout
  - **Details**: Position yellow box for new accounts count to align with data
  - **Priority**: Medium

### Medium Priority - Data & Analytics
- [ ] **Net Income Default Sort**: Set ascending by default in Territory views
  - **Location**: Territory view sorting
  - **Details**: Default sort by Net Income ascending
  - **Priority**: Medium

- [ ] **Pass Trash Accounts**: Handle missing M/C entirely
  - **Location**: Data processing logic
  - **Details**: Skip or handle accounts missing M/C data
  - **Priority**: Medium

- [ ] **Territory Trend Analysis**: Add territory trend functionality
  - **Location**: Analytics module
  - **Details**: Track and display territory performance trends
  - **Priority**: Medium

- [ ] **Account Trend Analysis**: Add account trend functionality
  - **Location**: Analytics module
  - **Details**: Track and display individual account trends
  - **Priority**: Medium

- [ ] **Rep Performance Tracking**: Track how rep is doing since coming on board
  - **Location**: Analytics module
  - **Details**: Measure rep performance over time
  - **Priority**: Medium

- [ ] **Dormant/Inactive Accounts**: Create list of dormant/inactive accounts
  - **Location**: Account management
  - **Details**: Identify and display inactive accounts
  - **Priority**: Medium

- [ ] **Territory Monthly Spend Comparison**: Compare monthly spend across territories
  - **Location**: Analytics module
  - **Details**: Monthly spend comparison functionality
  - **Priority**: Medium

### High Priority - AI Integration
- [x] **AI Summary Section**: Add AI pro/con analysis and action suggestions
  - **Location**: Dashboard bottom section
  - **Details**: Connect OpenAI API to provide AI-powered insights
  - **Priority**: High
  - **Status**: ✅ Completed - Created `/dev/ai-summary` endpoint with OpenAI integration and fallback mock analysis

- [ ] **AI Account Analysis**: Analyze average sized account w/o collector
  - **Location**: AI analytics module
  - **Details**: Determine how many collectors needed to hit metrics
  - **Priority**: High

- [ ] **AI Summary Dashboard**: Comprehensive AI analysis
  - **Location**: AI dashboard section
  - **Details**: Check specialty, ROS, Payer Mix, EPS, # of accounts, # of new accounts, Sample volume account concentration, Net Income. Show what's going well, what's a problem, and suggested actions including FOCUS on key accounts list and consider shaping or dropping list
  - **Priority**: High

### Low Priority - Technical Improvements
- [ ] **Encode/Decode Check**: Verify encode/decode functions in codebase
  - **Location**: Code review
  - **Details**: Check for proper encoding/decoding functions
  - **Priority**: Low

- [ ] **Convert to .NET**: Migrate from current stack to .NET
  - **Location**: Full application
  - **Details**: Major platform migration
  - **Priority**: Low

- [ ] **Specialty Identification**: Identify specialties in data
  - **Location**: Data analysis module
  - **Details**: Add specialty identification functionality
  - **Priority**: Low

- [ ] **ROS Target Analysis**: Determine ROS target and show comparison
  - **Location**: Analytics module
  - **Details**: What is target? How do we show ROS comparison of all territories?
  - **Priority**: Low

---

## Implementation Status
- **Total Changes**: 25
- **Completed**: 2
- **Pending**: 23

### Priority Breakdown
- **High Priority**: 4 items remaining (2 completed)
- **Medium Priority**: 16 items  
- **Low Priority**: 3 items

## Notes
- Add changes as you identify them
- Mark completed items with [x]
- Update status counts as you progress 
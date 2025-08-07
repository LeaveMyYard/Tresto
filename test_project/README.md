# TaskMaster - React Test Application

A simple task management application built with React and Vite for testing E2E automation tools like Tresto.

## Features

- **User Authentication**: Simple login system with demo credentials
- **Task Management**: Create, complete, and delete tasks
- **Local Storage**: Persistent data storage in browser localStorage
- **Statistics**: Track total, pending, and completed tasks
- **Responsive Design**: Works on desktop and mobile devices
- **Test-Ready**: Comprehensive data-testid attributes for E2E testing

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

The application will be available at `http://localhost:3000`.

## Demo Credentials

For testing purposes, you can use:
- **Username**: `admin`
- **Password**: `password`

Or any username with 3+ characters and password with 6+ characters.

## Application Structure

```
src/
├── components/
│   ├── LoginForm.jsx     # Authentication component
│   ├── LoginForm.css     # Login styling
│   ├── TaskManager.jsx   # Main task management component
│   └── TaskManager.css   # Task manager styling
├── App.jsx               # Main application component
├── App.css               # Global styles
└── main.jsx              # Application entry point
```

## E2E Testing Features

This application is designed to be tested with E2E automation tools and includes:

### Data Test IDs

All interactive elements include `data-testid` attributes:

#### Authentication
- `login-container` - Main login container
- `login-form` - Login form element
- `username-input` - Username input field
- `password-input` - Password input field
- `login-button` - Login submit button
- `username-error`, `password-error`, `general-error` - Error messages

#### Task Management
- `task-manager` - Main task manager container
- `welcome-message` - Welcome text with username
- `logout-button` - Logout button
- `task-stats` - Statistics container
- `total-tasks`, `pending-tasks`, `completed-tasks` - Task counters
- `add-task-form` - New task form
- `new-task-input` - New task input field
- `add-task-button` - Add task button
- `task-list` - Task list container
- `task-item-{id}` - Individual task items
- `task-checkbox-{id}` - Task completion checkboxes
- `task-text-{id}` - Task text content
- `delete-task-{id}` - Delete task buttons

### User Flows for Testing

1. **Login Flow**:
   - Navigate to application
   - Enter credentials
   - Submit form
   - Verify successful authentication

2. **Task Creation Flow**:
   - Add new task via input form
   - Verify task appears in list
   - Check task statistics update

3. **Task Management Flow**:
   - Mark tasks as complete/incomplete
   - Delete tasks
   - Verify persistence with page refresh

4. **Logout Flow**:
   - Click logout button
   - Verify return to login screen

## Data Persistence

- User tasks are stored in browser localStorage
- Data persists across browser sessions
- Each user has separate task storage
- Tasks include: ID, text, completion status, and creation timestamp

## Technologies Used

- **React 18** - UI library
- **Vite** - Build tool and dev server
- **Lucide React** - Icon library
- **CSS3** - Styling with gradients and animations
- **localStorage API** - Client-side data persistence

## Testing Recommendations

When writing E2E tests for this application:

1. **Use the provided data-testid attributes** for reliable element selection
2. **Test error states** by submitting invalid forms
3. **Verify data persistence** by refreshing the page
4. **Test responsive behavior** on different screen sizes
5. **Use realistic test data** with various task lengths and characters

## License

This project is created for testing purposes and is available under the MIT License.

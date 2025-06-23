# Crime Mapping Visualization

A modern web application for crime mapping and visualization with a React frontend and Flask API backend.

## 🚀 Features

- **Interactive Crime Map**: Visualize crime locations using Leaflet maps
- **Dashboard Analytics**: Charts and statistics for crime data analysis
- **User Authentication**: Secure login and registration system
- **Barangay Management**: Manage different barangay areas
- **Audit Logs**: Track system activities and user actions
- **Crime Report Upload**: Upload and manage crime reports
- **Responsive Design**: Modern UI with Bootstrap components

## 🛠️ Technology Stack

### Frontend (React)
- React 18
- React Router for navigation
- React Bootstrap for UI components
- Leaflet for interactive maps
- Chart.js for data visualization
- Axios for API communication

### Backend (Flask)
- Flask web framework
- Flask-Login for authentication
- MySQL database
- Pandas for data processing
- OpenPyXL for Excel file handling

## 📋 Prerequisites

- Node.js (v16 or higher)
- Python (v3.8 or higher)
- MySQL database
- npm or yarn package manager

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd crime_mapping_visualization
```

### 2. Backend Setup (Flask)

#### Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### Configure Database
1. Create a MySQL database
2. Update `config.py` with your database credentials:
```python
class Config:
    SECRET_KEY = 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = 'mysql://username:password@localhost/database_name'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
```

#### Run Flask Backend
```bash
python run.py
```
The Flask API will run on `http://localhost:5000`

### 3. Frontend Setup (React)

#### Install Node.js Dependencies
```bash
npm install
```

#### Start React Development Server
```bash
npm start
```
The React app will run on `http://localhost:3000`

## 📁 Project Structure

```
crime_mapping_visualization/
├── app/                    # Flask backend
│   ├── __init__.py        # Flask app initialization
│   ├── models.py          # Database models
│   ├── routes/            # API routes
│   ├── templates/         # HTML templates (legacy)
│   └── static/            # Static files (legacy)
├── src/                   # React frontend
│   ├── components/        # Reusable React components
│   ├── pages/            # Page components
│   ├── context/          # React context providers
│   ├── App.js            # Main App component
│   └── index.js          # React entry point
├── public/               # Public assets
├── package.json          # Node.js dependencies
├── requirements.txt      # Python dependencies
└── run.py               # Flask entry point
```

## 🔧 API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/user/profile` - Get user profile

### Crime Data
- `GET /api/crimes` - Get all crimes
- `POST /api/crimes` - Create new crime report
- `GET /api/crimes/{id}` - Get specific crime

### Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics

### Barangays
- `GET /api/barangays` - Get all barangays
- `POST /api/barangays` - Create new barangay

## 🎨 Customization

### Styling
- Modify `src/index.css` for global styles
- Use Bootstrap classes for component styling
- Custom CSS classes are available for specific components

### Map Configuration
- Update map center coordinates in `src/pages/CrimeMap.js`
- Modify marker colors and icons as needed
- Add custom map layers or tile providers

### Charts
- Customize chart colors and styles in `src/pages/Dashboard.js`
- Add new chart types using Chart.js
- Modify data sources and API endpoints

## 🔒 Security Features

- JWT token-based authentication
- Password hashing with Werkzeug
- CSRF protection
- Input validation and sanitization
- Secure session management

## 📊 Data Visualization

The application includes several types of visualizations:
- **Line Charts**: Crime trends over time
- **Bar Charts**: Crimes by barangay
- **Doughnut Charts**: Crime type distribution
- **Interactive Maps**: Geographic crime visualization

## 🚀 Deployment

### Production Build
```bash
# Build React app
npm run build

# Serve with Flask
python run.py
```

### Environment Variables
Create a `.env` file for production:
```
FLASK_ENV=production
SECRET_KEY=your-production-secret-key
DATABASE_URL=your-production-database-url
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the code comments

## 🔄 Migration from Flask Templates

This project has been migrated from Flask templates to React. The original Flask templates are preserved in `app/templates/` for reference.

### Key Changes:
- Frontend moved from server-side rendering to client-side React
- API endpoints added for data communication
- Authentication system updated to use JWT tokens
- Interactive maps and charts added
- Modern responsive UI with Bootstrap components 
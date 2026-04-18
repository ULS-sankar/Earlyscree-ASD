# Early Screen ASD - TV Application

A TV-optimized web application for analyzing videos to detect potential signs of autism spectrum disorder in children.

## Features

### 🏠 Home Screen
- **Logo Display**: Prominently displays the Early Screen ASD logo
- **Title**: "Early Screen ASD" with gradient styling
- **Three Main Buttons**:
  - **Upload Video**: Navigate to video analysis functionality
  - **View Reports**: Access history of past video analyses
  - **Learn More**: View detailed information and disclaimers

### 📹 Upload Video Screen
- **Drag & Drop Interface**: TV-friendly file upload area
- **File Browser**: Alternative method to select video files
- **Analysis Progress**: Real-time progress bar with status updates
- **Results Display**: Comprehensive analysis results including:
  - Overall assessment (Low/Moderate/High Probability)
  - Confidence score percentage
  - Analysis time
  - Detailed behavior analysis (Hand Flapping, Body Spinning, etc.)

### 📊 View Reports Screen
- **Search Functionality**: Filter reports by filename or date
- **Report History**: Complete list of past video analyses
- **Quick Summary**: Key metrics for each report
- **Report Details**: Click any report to view full analysis results

### ℹ️ Learn More Screen
- **Important Disclaimer**: Clear warnings about the tool's purpose
- **Detailed Information**: Comprehensive explanation of the system
- **How It Works**: Step-by-step process explanation
- **What We Analyze**: Specific behaviors and patterns detected
- **Benefits of Early Detection**: Information about early intervention
- **Privacy & Security**: Commitment to data protection

## Technical Specifications

### TV-Friendly Design
- **Large Text**: Optimized font sizes for viewing from a distance
- **High Contrast**: Clear visibility on TV screens
- **Simple Navigation**: Easy to use with TV remotes
- **Responsive Layout**: Adapts to different screen sizes

### Technologies Used
- **HTML5**: Semantic structure and accessibility
- **CSS3**: Modern styling with CSS Grid and Flexbox
- **JavaScript ES6+**: Interactive functionality and state management
- **Local Storage**: Persistent report storage

### Browser Compatibility
- Modern browsers with HTML5 support
- Optimized for Chrome, Firefox, Safari, and Edge
- Mobile-friendly responsive design

## Installation & Usage

### Quick Start
1. Download or clone the `tv_app` folder
2. Open `index.html` in any modern web browser
3. The application will load automatically

### No Server Required
This is a standalone web application that runs directly in your browser without requiring:
- Web server setup
- Database installation
- Backend services
- Internet connection (except for Google Fonts)

## File Structure
```
tv_app/
├── index.html          # Main HTML structure
├── styles.css          # TV-optimized CSS styles
├── script.js           # JavaScript functionality
└── README.md           # This documentation file
```

## Features Details

### Video Analysis Simulation
The application simulates video analysis with:
- **Realistic Progress Updates**: Step-by-step analysis messages
- **Randomized Results**: Different outcomes for each analysis
- **Behavior Detection**: Simulated detection of autism-related behaviors
- **Confidence Scoring**: Probability assessment based on detected behaviors

### Report Management
- **Automatic Saving**: Reports saved to browser local storage
- **Persistent Storage**: Reports remain available between sessions
- **Search & Filter**: Find specific reports quickly
- **Detailed View**: Complete analysis results for each report

### Accessibility Features
- **Keyboard Navigation**: Full keyboard support
- **High Contrast Mode**: Automatic adaptation
- **Reduced Motion**: Respects user motion preferences
- **Focus Indicators**: Clear visual focus for navigation

## Disclaimer

**Important**: Early Screen ASD is an assistive tool designed to help identify potential signs of autism spectrum disorder in children through video analysis. This tool is NOT a diagnostic tool and should not be used as a substitute for professional medical evaluation.

Always consult with qualified healthcare professionals for accurate diagnosis and treatment recommendations.

## Privacy & Security

- **Local Processing**: All data stays on your device
- **No Cloud Storage**: Reports stored only in browser local storage
- **No Data Sharing**: Information never leaves your browser
- **Automatic Cleanup**: Option to clear all stored data

## Development

### Customization
The application is designed to be easily customizable:
- **Colors**: Modify CSS variables in `styles.css`
- **Text**: Update content in `index.html`
- **Functionality**: Extend JavaScript in `script.js`
- **Styling**: Add new CSS classes and styles

### Future Enhancements
Potential improvements include:
- Integration with actual video analysis APIs
- Cloud-based report storage
- Multi-user support
- Advanced search and filtering
- Export functionality for reports

## Support

For questions or support:
- Check this README for common issues
- Ensure you're using a modern browser
- Verify JavaScript is enabled
- Clear browser cache if experiencing issues

## License

This application is provided as-is for educational and demonstration purposes. Please ensure compliance with local regulations regarding medical software and data privacy when using or modifying this application.
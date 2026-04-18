from report_generator import generate_pdf_report
try:
    results = {
        'is_conclusive': True,
        'dominant_behavior': 'Spinning',
        'dominant_behavior_label': 'Body Spinning',
        'model_confidence': 0.524,
        'behavior_percentages': {'Armflapping': 19.0, 'Headbanging': 28.6, 'Spinning': 52.4, 'Normal': 0.0},
        'file_path': 'C:/path/test 1.mp4'
    }
    generate_pdf_report(results, "test_report.pdf")
    print("PDF generation successful!")
except Exception as e:
    import traceback
    traceback.print_exc()

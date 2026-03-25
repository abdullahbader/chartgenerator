import 'package:flutter/material.dart';
import 'package:flutter_colorpicker/flutter_colorpicker.dart';
import 'dart:convert';
import '../services/api_service.dart';
import '../models/chart_type.dart';
import '../models/dataset.dart';
import 'chart_preview_screen.dart';

class ChartCustomizationScreen extends StatefulWidget {
  final ChartType chartType;
  final Dataset dataset;
  final String selectedColumn;

  const ChartCustomizationScreen({
    super.key,
    required this.chartType,
    required this.dataset,
    required this.selectedColumn,
  });

  @override
  State<ChartCustomizationScreen> createState() =>
      _ChartCustomizationScreenState();
}

class _ChartCustomizationScreenState extends State<ChartCustomizationScreen> {
  final ApiService _apiService = ApiService();
  final TextEditingController _titleController = TextEditingController();
  
  String _fontFamily = 'Arial';
  double _fontSize = 12.0;
  List<Color> _colors = [
    Colors.blue,
    Colors.orange,
    Colors.green,
    Colors.red,
    Colors.purple,
  ];
  bool _isGenerating = false;

  final List<String> _fontFamilies = [
    'Arial',
    'Times New Roman',
    'Courier New',
    'Verdana',
    'Georgia',
    'Helvetica',
  ];

  @override
  void initState() {
    super.initState();
    _titleController.text = 'Pie Chart: ${widget.selectedColumn}';
  }

  @override
  void dispose() {
    _titleController.dispose();
    super.dispose();
  }

  Future<void> _generateChart() async {
    setState(() {
      _isGenerating = true;
    });

    try {
      final customization = {
        'title': _titleController.text,
        'font_family': _fontFamily,
        'font_size': _fontSize.toInt(),
        'colors': _colors.map((c) => '#${c.value.toRadixString(16).substring(2)}').toList(),
      };

      final chartData = await _apiService.generateChart(
        chartType: widget.chartType.id,
        datasetId: widget.dataset.id,
        column: widget.selectedColumn,
        customization: customization,
      );

      if (mounted) {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => ChartPreviewScreen(
              chartType: widget.chartType,
              dataset: widget.dataset,
              selectedColumn: widget.selectedColumn,
              customization: customization,
              chartData: chartData,
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error generating chart: $e')),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isGenerating = false;
        });
      }
    }
  }

  void _showColorPicker(int index) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Pick Color ${index + 1}'),
        content: SingleChildScrollView(
          child: ColorPicker(
            pickerColor: _colors[index],
            onColorChanged: (color) {
              setState(() {
                _colors[index] = color;
              });
            },
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Done'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Customize Chart'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Title
            TextField(
              controller: _titleController,
              decoration: const InputDecoration(
                labelText: 'Chart Title',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 24),

            // Font Family
            const Text(
              'Font Family',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              value: _fontFamily,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
              ),
              items: _fontFamilies.map((font) {
                return DropdownMenuItem(
                  value: font,
                  child: Text(font),
                );
              }).toList(),
              onChanged: (value) {
                if (value != null) {
                  setState(() {
                    _fontFamily = value;
                  });
                }
              },
            ),
            const SizedBox(height: 24),

            // Font Size
            const Text(
              'Font Size',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: Slider(
                    value: _fontSize,
                    min: 8,
                    max: 24,
                    divisions: 16,
                    label: _fontSize.toInt().toString(),
                    onChanged: (value) {
                      setState(() {
                        _fontSize = value;
                      });
                    },
                  ),
                ),
                Text(
                  _fontSize.toInt().toString(),
                  style: const TextStyle(fontSize: 16),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Colors
            const Text(
              'Colors',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 16,
              runSpacing: 16,
              children: List.generate(
                _colors.length,
                (index) => GestureDetector(
                  onTap: () => _showColorPicker(index),
                  child: Container(
                    width: 60,
                    height: 60,
                    decoration: BoxDecoration(
                      color: _colors[index],
                      shape: BoxShape.circle,
                      border: Border.all(color: Colors.grey, width: 2),
                    ),
                    child: Center(
                      child: Text(
                        '${index + 1}',
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 32),

            // Generate Button
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                onPressed: _isGenerating ? null : _generateChart,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue,
                  foregroundColor: Colors.white,
                ),
                child: _isGenerating
                    ? const CircularProgressIndicator(color: Colors.white)
                    : const Text(
                        'Generate Chart',
                        style: TextStyle(fontSize: 18),
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

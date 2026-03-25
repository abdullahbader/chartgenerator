import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'screens/chart_selection_screen.dart';

void main() {
  runApp(const ChartsGeneratorApp());
}

class ChartsGeneratorApp extends StatelessWidget {
  const ChartsGeneratorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Charts Generator',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const ChartSelectionScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}

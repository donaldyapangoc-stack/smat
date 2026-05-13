import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';

class AddEstacionScreen extends StatefulWidget {
  @override
  _AddEstacionScreenState createState() => _AddEstacionScreenState();
}

class _AddEstacionScreenState extends State<AddEstacionScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nombreController = TextEditingController();
  final _ubicacionController = TextEditingController();

  void _guardar() async {
    if (_formKey.currentState!.validate()) {
      bool success = await ApiService().crearEstacion(
        _nombreController.text,
        _ubicacionController.text
      );
      if (success) {
        Navigator.pop(context, true); // Regresa al Dashboard
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: No autorizado o Servidor caído')),
        );
      }
    }
  }  // ← Cierre del método _guardar

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Nueva Estación')),
      body: Form(
        key: _formKey,
        child: Padding(
          padding: const EdgeInsets.all(16),  // ← Agregar 'const'
          child: Column(
            children: [
              TextFormField(
                controller: _nombreController,
                decoration: InputDecoration(labelText: 'Nombre'),
                validator: (v) => v!.isEmpty ? 'Requerido' : null,
              ),
              TextFormField(
                controller: _ubicacionController,
                decoration: InputDecoration(labelText: 'Ubicación'),
                validator: (v) => v!.isEmpty ? 'Requerido' : null,
              ),
              const SizedBox(height: 20),  // ← Agregar 'const'
              ElevatedButton(
                onPressed: _guardar, 
                child: Text('Guardar Estación')
              ),
            ],
          ),
        ),
      ),
    );
  }  
}  
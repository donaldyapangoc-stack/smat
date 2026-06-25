extends Node2D

func actualizar_estado(valor):
	$Label.text = str(valor) + " cm"
	if float(valor) > 70:
		$Sprite2D.modulate = Color.RED
	else:
		$Sprite2D.modulate = Color.GREEN

import cameraPrinter

printer = cameraPrinter.CameraPrinter(daemon=True, pixelHeight=512, pixelWidth=512)
printer.loop()

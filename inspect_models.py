import backend.app as app_mod
m = getattr(app_mod, 'ELIGIBILITY_MODELS', None)
print('ELIGIBILITY_MODELS is', type(m))
if m:
    print('classifier:', bool(m.get('classifier')))
    print('predictor:', bool(m.get('predictor')))
    print('scaler:', bool(m.get('scaler')))
    print('encoders:', bool(m.get('encoders')))
else:
    print('No models loaded')

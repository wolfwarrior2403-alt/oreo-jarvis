import React, {useEffect, useRef} from 'react';
import {Animated, Easing, StyleSheet, View} from 'react-native';

/** Simple animated waveform bars shown while actively listening/streaming
 * audio (section 4.2, "waveform animation when active"). Passive/idle state
 * renders a static dot instead — see HomeScreen. */
export default function WaveformIndicator({active}: {active: boolean}) {
  const bars = useRef([...Array(5)].map(() => new Animated.Value(0.3))).current;

  useEffect(() => {
    if (!active) {
      bars.forEach(bar => bar.setValue(0.3));
      return;
    }
    const loops = bars.map((bar, i) =>
      Animated.loop(
        Animated.sequence([
          Animated.timing(bar, {
            toValue: 1,
            duration: 300 + i * 60,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: false,
          }),
          Animated.timing(bar, {
            toValue: 0.3,
            duration: 300 + i * 60,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: false,
          }),
        ]),
      ),
    );
    loops.forEach(loop => loop.start());
    return () => loops.forEach(loop => loop.stop());
  }, [active, bars]);

  return (
    <View style={styles.row}>
      {bars.map((bar, i) => (
        <Animated.View
          key={i}
          style={[
            styles.bar,
            {
              height: bar.interpolate({inputRange: [0, 1], outputRange: [8, 48]}),
            },
          ]}
        />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    height: 56,
  },
  bar: {
    width: 6,
    borderRadius: 3,
    backgroundColor: '#6C5CE7',
  },
});
